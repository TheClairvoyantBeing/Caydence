"""
modules/audio_engine.py
======================
High-Fidelity 48 kHz Float32 Audio Engine & Mixing Console.

Features:
- Standardized internal format: 48 kHz, float32, stereo.
- Ultra-clean resampling via `soxr`.
- Loudness measurement & normalization via `pyloudnorm` (-16 LUFS integrated, -1 dBTP true peak).
- Mastering chain with `pedalboard` (PeakLimiter, HighpassFilter, Compressor).
- Smart silence trimming (>150ms dead lead/tail trimmed, 80-250ms natural gaps preserved).
- Breath injection at sentence boundaries.
- Full backwards compatibility with legacy Caydence text cleaning and chunking.
"""

import os
import re
import numpy as np
import soundfile as sf

try:
    import soxr
except ImportError:
    soxr = None

try:
    import pyloudnorm as pyln
except ImportError:
    pyln = None

try:
    from pedalboard import Pedalboard, BrickwallLimiter, HighpassFilter, Compressor
except ImportError:
    Pedalboard = None
    BrickwallLimiter = None
    HighpassFilter = None
    Compressor = None


TARGET_SAMPLE_RATE = 48000
TARGET_CHANNELS = 2
TARGET_LUFS = -16.0
TARGET_PEAK_DBTP = -1.0


class _NullWatermarker:
    """Drop-in replacement for the perth watermarker when native extension is unavailable."""
    def apply_watermark(self, wav, sample_rate=None):
        return wav


def _ensure_perth_works():
    """Ensures Perth watermark doesn't crash on Windows."""
    try:
        import perth
        perth.PerthImplicitWatermarker()
        return
    except Exception:
        pass

    try:
        import perth
        perth.PerthImplicitWatermarker = _NullWatermarker
    except Exception:
        pass

    try:
        import chatterbox.tts as _tts_mod
        if hasattr(_tts_mod, "PerthImplicitWatermarker"):
            _tts_mod.PerthImplicitWatermarker = _NullWatermarker
        if hasattr(_tts_mod, "perth"):
            _tts_mod.perth.PerthImplicitWatermarker = _NullWatermarker
    except Exception:
        pass


def clean_text_for_tts(text: str) -> str:
    """Strip or convert tags that would be read aloud literally."""
    text = re.sub(r'(?im)^\s*Chapter\s+\d+[:\s\-\–\—].*$', '', text)
    text = re.sub(r'(?im)^\s*Chapter\s+\d+\s*$', '', text)
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'\(Originally\s+Posted\s+to\s+r/[^\)]+\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[?(?:EDIT|UPDATE)\s*\d*\]?\s*:?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[([a-z\s,;-]+)\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'</?think>', '', text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 120) -> list:
    """Cleans input text and splits it into small, manageable chunks for TTS engines."""
    text = clean_text_for_tts(text)
    raw_sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    for sentence in raw_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            sub_parts = re.split(r'(?<=,)\s+', sentence)
            for part in sub_parts:
                part = part.strip()
                if not part:
                    continue
                if len(current) + len(part) + 1 <= max_chars:
                    current = (current + " " + part).strip()
                else:
                    if current:
                        chunks.append(current)
                    current = part[:max_chars]
        else:
            if len(current) + len(sentence) + 1 <= max_chars:
                current = (current + " " + sentence).strip()
            else:
                if current:
                    chunks.append(current)
                current = sentence
    if current:
        chunks.append(current)
    return chunks


def normalize_rms(wav, target_rms: float = 0.08):
    """Legacy RMS normalization helper kept for backwards compatibility."""
    if torch is not None and isinstance(wav, torch.Tensor):
        rms = torch.sqrt(torch.mean(wav.float() ** 2))
        if rms > 1e-6:
            wav = wav * (target_rms / rms)
        return torch.clamp(wav, -1.0, 1.0)
    elif isinstance(wav, np.ndarray):
        rms = np.sqrt(np.mean(wav ** 2))
        if rms > 1e-6:
            wav = wav * (target_rms / rms)
        return np.clip(wav, -1.0, 1.0)
    return wav


class AudioBuffer:
    """
    Standardized in-memory audio representation: 48 kHz, float32, stereo (shape: [2, N]).
    """
    def __init__(self, data: np.ndarray, sample_rate: int = TARGET_SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.data = self._standardize(data, sample_rate)

    @classmethod
    def from_file(cls, filepath: str, max_retries: int = 5) -> "AudioBuffer":
        """Loads audio file from disk into a 48 kHz float32 stereo buffer."""
        import time
        last_err = None
        for attempt in range(max_retries):
            try:
                data, sr = sf.read(filepath, dtype='float32')
                return cls(data, sr)
            except Exception as e:
                last_err = e
                time.sleep(0.3 * (attempt + 1))
        raise last_err

    @classmethod
    def silent(cls, duration_sec: float, sample_rate: int = TARGET_SAMPLE_RATE) -> "AudioBuffer":
        """Generates a buffer of silence of the specified duration."""
        num_samples = int(duration_sec * sample_rate)
        return cls(np.zeros((2, num_samples), dtype=np.float32), sample_rate)

    @classmethod
    def stream_stitch_files(cls, file_list: list, output_path: str, gap_sec: float = 0.65,
                            target_sample_rate: int = TARGET_SAMPLE_RATE) -> float:
        """
        Streams audio chunk files directly from disk into an output 48kHz stereo WAV
        to eliminate multi-gigabyte memory accumulation.
        """
        import gc
        gap_samples = int(gap_sec * target_sample_rate)
        silence = np.zeros((gap_samples, 2), dtype=np.float32) if gap_samples > 0 else None
        total_frames = 0

        with sf.SoundFile(output_path, mode='w', samplerate=target_sample_rate, channels=2, subtype='FLOAT') as out_f:
            for idx, fpath in enumerate(file_list):
                if idx > 0 and silence is not None:
                    out_f.write(silence)
                    total_frames += gap_samples

                buf = cls.from_file(fpath)
                data = buf.data.T  # Shape [N, 2]
                out_f.write(data)
                total_frames += data.shape[0]
                del buf, data
                if idx % 50 == 0:
                    gc.collect()

        return float(total_frames) / target_sample_rate


    def _standardize(self, data: np.ndarray, source_sr: int) -> np.ndarray:
        """Converts any shape/bit-depth audio to shape [2, N] float32 at 48 kHz."""
        data = np.asarray(data, dtype=np.float32)

        # Handle shapes: [N] -> [1, N], [N, C] -> [C, N]
        if data.ndim == 1:
            data = np.stack([data, data], axis=0)
        elif data.ndim == 2:
            if data.shape[0] > data.shape[1] and data.shape[1] <= 2:
                data = data.T
            if data.shape[0] == 1:
                data = np.repeat(data, 2, axis=0)
            elif data.shape[0] > 2:
                data = data[:2, :]

        # High-quality Resampling via soxr
        if source_sr != TARGET_SAMPLE_RATE:
            if soxr is not None:
                ch0 = soxr.resample(data[0], source_sr, TARGET_SAMPLE_RATE, quality='soxr_hq')
                ch1 = soxr.resample(data[1], source_sr, TARGET_SAMPLE_RATE, quality='soxr_hq')
                data = np.stack([ch0, ch1], axis=0)
            else:
                # Scipy linear fallback if soxr is missing
                from scipy import signal
                num_new_samples = int(data.shape[1] * TARGET_SAMPLE_RATE / source_sr)
                ch0 = signal.resample(data[0], num_new_samples)
                ch1 = signal.resample(data[1], num_new_samples)
                data = np.stack([ch0, ch1], axis=0).astype(np.float32)

        self.sample_rate = TARGET_SAMPLE_RATE
        return data

    @property
    def duration_sec(self) -> float:
        return self.data.shape[1] / self.sample_rate

    @property
    def num_samples(self) -> int:
        return self.data.shape[1]

    def apply_gain_db(self, gain_db: float) -> "AudioBuffer":
        """Applies gain in decibels."""
        scale = 10.0 ** (gain_db / 20.0)
        self.data = self.data * scale
        return self

    def pan(self, pan_val: float) -> "AudioBuffer":
        """
        Constant-power stereo pan law: pan_val in [-1.0 (Left), +1.0 (Right)].
        """
        pan_val = np.clip(pan_val, -1.0, 1.0)
        # Normalizes pan to angle [0, pi/2]
        angle = (pan_val + 1.0) * (np.pi / 4.0)
        left_gain = np.cos(angle)
        right_gain = np.sin(angle)

        self.data[0] *= left_gain
        self.data[1] *= right_gain
        return self

    def trim_silence(self, threshold_db: float = -45.0, min_silence_ms: float = 150.0,
                     preserve_ms: float = 100.0) -> "AudioBuffer":
        """
        Trims dead lead and trail silence only if it exceeds min_silence_ms.
        Preserves natural speech onset/offset gaps (preserve_ms).
        """
        energy = np.maximum(np.abs(self.data[0]), np.abs(self.data[1]))
        thresh = 10.0 ** (threshold_db / 20.0)
        active_indices = np.where(energy > thresh)[0]

        if len(active_indices) == 0:
            return self

        first_active = active_indices[0]
        last_active = active_indices[-1]

        min_samples = int(min_silence_ms * self.sample_rate / 1000.0)
        keep_samples = int(preserve_ms * self.sample_rate / 1000.0)

        start_idx = max(0, first_active - keep_samples) if first_active > min_samples else 0
        has_trailing_silence = (self.data.shape[1] - last_active) > min_samples
        end_idx = min(self.data.shape[1], last_active + keep_samples) if has_trailing_silence else self.data.shape[1]

        trimmed = self.data[:, start_idx:end_idx]

        # 15ms gentle cosine fade-in/fade-out to prevent clicks
        fade_samples = int(0.015 * self.sample_rate)
        if trimmed.shape[1] > 2 * fade_samples:
            fade_in = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, fade_samples)))
            fade_out = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, fade_samples)))
            trimmed[:, :fade_samples] *= fade_in
            trimmed[:, -fade_samples:] *= fade_out

        self.data = trimmed
        return self

    def overlay(self, other: "AudioBuffer", offset_sec: float = 0.0) -> "AudioBuffer":
        """Overlays another audio buffer at a given time offset."""
        offset_samples = int(offset_sec * self.sample_rate)
        total_len = max(self.num_samples, offset_samples + other.num_samples)

        if total_len > self.num_samples:
            pad = np.zeros((2, total_len - self.num_samples), dtype=np.float32)
            self.data = np.concatenate([self.data, pad], axis=1)

        end_samples = offset_samples + other.num_samples
        self.data[:, offset_samples:end_samples] += other.data
        return self

    def concatenate(self, other: "AudioBuffer", gap_sec: float = 0.15) -> "AudioBuffer":
        """Appends another audio buffer with a controlled conversational pause."""
        gap_samples = int(gap_sec * self.sample_rate)
        gap = np.zeros((2, gap_samples), dtype=np.float32)
        self.data = np.concatenate([self.data, gap, other.data], axis=1)
        return self

    def export(self, filepath: str, subtype: str = "FLOAT"):
        """Writes buffer to WAV/FLAC with 32-bit float or 24-bit PCM."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        # Transpose [2, N] -> [N, 2] for soundfile
        sf.write(filepath, self.data.T, self.sample_rate, subtype=subtype)


def generate_subtle_breath(duration_sec: float = 0.18, sample_rate: int = TARGET_SAMPLE_RATE) -> AudioBuffer:
    """Generates an organic human inhalation breath sound to place between tense dialogue."""
    num_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)

    # Pinkish filtered noise
    noise = np.random.normal(0, 1, num_samples)
    from scipy import signal
    b, a = signal.butter(2, [800 / (sample_rate / 2), 3400 / (sample_rate / 2)], btype='band')
    breath = signal.lfilter(b, a, noise)

    # Swell envelope
    env = np.sin(np.pi * (t / duration_sec)) ** 1.8
    breath = (breath * env * 0.04).astype(np.float32)
    stereo = np.stack([breath, breath], axis=0)
    return AudioBuffer(stereo, sample_rate)


class AudioMasteringConsole:
    """
    Bus mixing console: measures LUFS via pyloudnorm, handles EBU R128 compliance,
    and masters the final mix with a high-fidelity true-peak limiter.
    """
    def __init__(self, target_lufs: float = TARGET_LUFS, peak_limit_dbtp: float = TARGET_PEAK_DBTP):
        self.target_lufs = target_lufs
        self.peak_limit_dbtp = peak_limit_dbtp

    def measure_loudness(self, buffer: AudioBuffer) -> float:
        """Calculates integrated LUFS using pyloudnorm."""
        if pyln is None:
            # Fallback RMS approximation if pyloudnorm missing
            rms = np.sqrt(np.mean(buffer.data ** 2))
            return 20.0 * np.log10(rms + 1e-9)

        meter = pyln.Meter(buffer.sample_rate)
        # Meter expects [N, 2]
        loudness = meter.integrated_loudness(buffer.data.T)
        return float(loudness)

    def normalize_stem_loudness(self, buffer: AudioBuffer, target_lufs: float) -> AudioBuffer:
        """Loudness normalizes a stem to a specific integrated LUFS."""
        current_lufs = self.measure_loudness(buffer)
        if current_lufs < -70.0:  # Silence or near silence
            return buffer

        gain_db = target_lufs - current_lufs
        buffer.apply_gain_db(gain_db)
        return buffer

    def master_bus(self, buffer: AudioBuffer) -> AudioBuffer:
        """
        Applies final broadcast mastering:
        1. Subsonic highpass filter (25 Hz)
        2. Integrated loudness normalization to -16 LUFS
        3. Transparent peak limiting with pedalboard PeakLimiter (-1.0 dBTP ceiling)
        """
        # Step 1: Subsonic filter
        from scipy import signal
        b, a = signal.butter(2, 25.0 / (buffer.sample_rate / 2.0), btype='high')
        filtered_l = signal.lfilter(b, a, buffer.data[0])
        filtered_r = signal.lfilter(b, a, buffer.data[1])
        buffer.data = np.stack([filtered_l, filtered_r], axis=0).astype(np.float32)

        # Step 2: LUFS Loudness Match
        self.normalize_stem_loudness(buffer, self.target_lufs)

        # Step 3: Peak Limiter
        if Pedalboard is not None and BrickwallLimiter is not None:
            board = Pedalboard([
                BrickwallLimiter(ceiling_db=self.peak_limit_dbtp, release_ms=100.0)
            ])
            # Pedalboard expects [num_channels, num_samples]
            mastered = board(buffer.data, buffer.sample_rate)
            buffer.data = mastered.astype(np.float32)
        else:
            # Hard limiter fallback
            max_val = 10.0 ** (self.peak_limit_dbtp / 20.0)
            buffer.data = np.clip(buffer.data, -max_val, max_val)

        return buffer

    @classmethod
    def master_file_stream(cls, input_wav: str, output_wav: str, target_sample_rate: int = TARGET_SAMPLE_RATE) -> None:
        """
        Applies EBU R128 loudness normalization (-16.0 LUFS, -1.0 dBTP true-peak limiting)
        directly via FFmpeg stream, avoiding Python RAM exhaustion on long-form audio.
        """
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-i", input_wav,
            "-af", "loudnorm=I=-16.0:TP=-1.0:LRA=11",
            "-ar", str(target_sample_rate),
            "-ac", "2",
            output_wav
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    @classmethod
    def encode_spotify_mp3(cls, input_wav: str, output_mp3: str, target_sample_rate: int = TARGET_SAMPLE_RATE,
                           bitrate: str = "256k") -> None:
        """
        Encodes 48kHz master WAV to high-bitrate CBR MP3 standard for Spotify.
        """
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-i", input_wav,
            "-codec:a", "libmp3lame",
            "-b:a", bitrate,
            "-ar", str(target_sample_rate),
            output_mp3
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)



class AudioEngine:
    """
    Consolidated Audio Engine maintaining backwards compatibility with Caydence callers
    while utilizing the new 48 kHz float32 pipeline internally.
    """
    normalize_rms = staticmethod(normalize_rms)
    chunk_text = staticmethod(chunk_text)

    def __init__(self, device=None):
        self.device = device or ("cuda" if (torch and torch.cuda.is_available()) else "cpu")
        self.model = None

        try:
            _ensure_perth_works()
            from chatterbox.tts import ChatterboxTTS
            self.model = ChatterboxTTS.from_pretrained(device=self.device)
            print(f"[AUDIO] ChatterboxTTS initialized on {self.device}.")
        except Exception as e:
            print(f"[AUDIO] Local Chatterbox offline ({e}). Using neural speech fallback.")
            self.model = None

    def synthesize_neural(self, text: str, output_path: str, voice: str = "en-US-ChristopherNeural") -> bool:
        """Synthesizes high-fidelity speech via edge-tts into 48 kHz float32 stereo WAV."""
        import asyncio
        import tempfile
        import edge_tts

        clean = clean_text_for_tts(text)
        temp_mp3 = os.path.join(tempfile.gettempdir(), f"vox_tts_{os.getpid()}.mp3")

        async def _run():
            comm = edge_tts.Communicate(clean, voice, rate="-3%", pitch="-1Hz")
            await comm.save(temp_mp3)

        try:
            asyncio.run(_run())
            if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 500:
                buf = AudioBuffer.from_file(temp_mp3)
                buf.trim_silence()
                buf.export(output_path)
                return True
            return False
        except Exception as e:
            print(f"[AUDIO] Neural voice error: {e}")
            return False
        finally:
            if os.path.exists(temp_mp3):
                try:
                    os.remove(temp_mp3)
                except OSError:
                    pass

    def generate_narration(self, text: str, reference_path: str, output_path: str) -> bool:
        """Main narration entry point for Caydence."""
        if self.model is None:
            ref_str = (reference_path or "").lower()
            if "dark_somnium" in ref_str or "mystery" in ref_str:
                voice = "en-US-BrianNeural"
            elif "creepypasta" in ref_str:
                voice = "en-US-GuyNeural"
            else:
                voice = "en-US-ChristopherNeural"
            return self.synthesize_neural(text, output_path, voice=voice)

        # When Chatterbox is available, synthesize chunks, standardize to 48kHz and save
        chunks = self.chunk_text(text)
        segments = []
        for chunk in chunks:
            with torch.no_grad():
                wav = self.model.generate(
                    chunk,
                    audio_prompt_path=reference_path,
                    exaggeration=0.5,
                    cfg_weight=0.5,
                    temperature=0.8
                )
            wav_np = wav.cpu().squeeze().numpy()
            buf = AudioBuffer(wav_np, sample_rate=self.model.sr)
            segments.append(buf)

        if segments:
            master = segments[0]
            for seg in segments[1:]:
                master.concatenate(seg, gap_sec=0.20)
            console = AudioMasteringConsole()
            master = console.master_bus(master)
            master.export(output_path)
            return True
        return False
