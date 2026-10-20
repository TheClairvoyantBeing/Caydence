"""
modules/pipeline/synthesizer.py
===============================
Audio Synthesizer Engine for Caydence Long-Form Audio Production.
Handles gender-matched neural TTS, resilient chunk caching, 48 kHz float32 audio,
and broadcast mastering (-16 LUFS, -1 dBTP true-peak).
"""

import os
import sys
import shutil
import asyncio
import soundfile as sf
from ..audio_engine import AudioBuffer, AudioMasteringConsole, TARGET_SAMPLE_RATE

try:
    import edge_tts
except ImportError:
    edge_tts = None

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(MODULE_DIR))


class AudioSynthesizer:
    """Renders high-fidelity, gender-matched long-form audio into a single unified narration.wav."""

    MALE_VOICES = [
        "en-US-BrianNeural",    # Brian: Deep, resonant, late-night atmospheric
        "en-US-SteffanNeural",  # Steffan: Intense, dramatic, close-mic
        "en-CA-LiamNeural",     # Liam: Clean, balanced, modern Canadian
    ]

    FEMALE_VOICES = [
        "en-US-JennyNeural",    # Jenny: Expressive, clear, engaging American female
        "en-US-AnaNeural",      # Ana: Soft, youthful, vulnerable
    ]

    def __init__(self, logger=None):
        if edge_tts is None:
            raise ImportError("[ERROR] 'edge_tts' is required for AudioSynthesizer. Run pip install edge-tts.")
        self.log = logger or (lambda msg: print(msg, flush=True))
        self.mastering = AudioMasteringConsole()

    def get_voice(self, gender: str, sid: int = 1, preferred_voice: str = None) -> str:
        """Resolves narrator voice ID from approved voice pools, shifting based on gender and story ID."""
        if preferred_voice:
            return preferred_voice
        g = (gender or "male").lower()
        if g == "female":
            idx = ((sid - 1) // 2) if sid % 2 == 0 else (sid - 1)
            return self.FEMALE_VOICES[idx % len(self.FEMALE_VOICES)]
        else:
            idx = ((sid - 1) // 2) if sid % 2 == 1 else (sid - 1)
            return self.MALE_VOICES[idx % len(self.MALE_VOICES)]

    async def render_story_audio(self, sid: int, sinfo: dict, full_text: str, folder_path: str) -> dict:
        """Synthesizes text in isolated scratch chunks and stitches into a 48kHz float32 audio track."""
        gender = sinfo.get("gender", "male")
        voice = self.get_voice(gender, sid=sid, preferred_voice=sinfo.get("voice"))
        from .catalog import StoryCatalog
        canonical_name = StoryCatalog.get_audio_filename(sid, sinfo)
        canonical_wav = os.path.join(folder_path, canonical_name)
        legacy_wav = os.path.join(folder_path, "narration.wav")
        output_wav = canonical_wav
        temp_dir = os.path.join(REPO_ROOT, ".cache", f"render_cache_sid_{sid}")
        os.makedirs(temp_dir, exist_ok=True)

        self.log(f"  Selected smooth narrator voice: {voice} (Gender: {gender.upper()}) | Target: {canonical_name}")

        # Chunk text at paragraph and sentence boundaries (<1800 characters per chunk)
        # Note: _chunk_text automatically strips chapter numbers, titles, and metadata headers
        chunks = self._chunk_text(full_text, max_chars=1800)
        self.log(f"  Starting TTS rendering: {len(chunks)} chunks using {voice} (cached in scratch)...")

        temp_files = []
        try:
            for idx, chunk_text in enumerate(chunks, 1):
                chunk_file = os.path.join(temp_dir, f"chunk_{idx}.mp3")
                if os.path.exists(chunk_file) and os.path.getsize(chunk_file) > 1000:
                    temp_files.append(chunk_file)
                    continue

                max_retries = 6
                success = False
                for attempt in range(1, max_retries + 1):
                    try:
                        # Tuned to smooth, warm, relaxed storytelling pace (-8% rate, -2Hz pitch)
                        comm = edge_tts.Communicate(chunk_text, voice, rate="-8%", pitch="-2Hz")
                        await asyncio.wait_for(comm.save(chunk_file), timeout=120.0)
                        if os.path.exists(chunk_file) and os.path.getsize(chunk_file) > 1000:
                            temp_files.append(chunk_file)
                            success = True
                            break
                        else:
                            raise IOError("Downloaded chunk file was empty or corrupted.")
                    except Exception as e:
                        self.log(f"    [WARN] TTS Chunk {idx}/{len(chunks)} attempt {attempt} failed: {type(e).__name__} ({e}). Retrying in {attempt * 2}s...")
                        if os.path.exists(chunk_file):
                            try:
                                os.remove(chunk_file)
                            except OSError:
                                pass
                        await asyncio.sleep(attempt * 2)

                if not success:
                    raise RuntimeError(f"TTS Chunk {idx}/{len(chunks)} failed after {max_retries} attempts.")
                await asyncio.sleep(0.2)

            await asyncio.sleep(1.0)
            self.log(f"  Stitching {len(temp_files)} audio chunks into 48 kHz float32 {canonical_name}...")
            master_buffer = AudioBuffer.silent(0.5, TARGET_SAMPLE_RATE)
            for tf in temp_files:
                seg = AudioBuffer.from_file(tf)
                # Gentle silence trimming that preserves natural breath and sentence flow
                seg.trim_silence(threshold_db=-50.0, min_silence_ms=350.0, preserve_ms=200.0)
                # Natural 550ms breath pause between narrative blocks
                master_buffer.concatenate(seg, gap_sec=0.55)

            # Broadcast mastering: -16 LUFS integrated, -1 dBTP true peak limiting
            self.log("  Mastering track to EBU R128 (-16 LUFS, -1 dBTP true-peak)...")
            master_buffer = self.mastering.master_bus(master_buffer)
            master_buffer.export(canonical_wav)

            # Maintain legacy narration.wav link/copy for downstream compatibility
            if os.path.abspath(canonical_wav) != os.path.abspath(legacy_wav):
                try:
                    if os.path.exists(legacy_wav):
                        os.remove(legacy_wav)
                    os.link(canonical_wav, legacy_wav)
                except OSError:
                    shutil.copyfile(canonical_wav, legacy_wav)

            duration_min = master_buffer.duration_sec / 60.0
            size_mb = os.path.getsize(canonical_wav) / (1024 * 1024)
            measured_lufs = self.mastering.measure_loudness(master_buffer)

            self.log(f"  [AUDIO COMPLETE] Unified track created: Duration: {duration_min:.2f} min | File Size: {size_mb:.2f} MB | LUFS: {measured_lufs:.2f}")

            # Prune directory to strictly ensure no stray files
            self._prune_output_folder(folder_path)

            return {
                "wav_path": canonical_wav,
                "duration_min": duration_min,
                "size_mb": size_mb,
                "voice": voice,
                "lufs": measured_lufs
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def render_audio_drama(self, sid: int, sinfo: dict, script_path_or_text: str, folder_path: str) -> dict:
        """Renders full multi-people cinematic audio drama with separate stems and master mix (Type 2)."""
        from ..cue_sheet import CueSheetParser, AudioDramaProducer
        from ..voice_engine import CharacterVoiceManager
        from ..sound_design import SoundDesignEngine
        from ..spatial_mix import SpatialMixer

        os.makedirs(folder_path, exist_ok=True)
        temp_dir = os.path.join(REPO_ROOT, "scratch", f"render_cache_drama_{sid}")
        os.makedirs(temp_dir, exist_ok=True)

        # If passed raw text or path
        if os.path.exists(script_path_or_text):
            script_file = script_path_or_text
        else:
            script_file = os.path.join(folder_path, "story.md")
            with open(script_file, "w", encoding="utf-8") as f:
                f.write(script_path_or_text)

        self.log(f"  [TYPE 2 AUDIO DRAMA] Parsing cue sheet from: {script_file}")
        parser = CueSheetParser(script_file)
        timeline = parser.parse_to_timeline()
        events = timeline.get("events", [])
        self.log(f"  [TYPE 2 AUDIO DRAMA] Parsed {len(events)} cues (dialogue, SFX, overlap groups).")

        producer = AudioDramaProducer(
            char_manager=CharacterVoiceManager(),
            sound_engine=SoundDesignEngine(sample_rate=TARGET_SAMPLE_RATE),
            spatial_mixer=SpatialMixer(sample_rate=TARGET_SAMPLE_RATE)
        )

        results = await producer.produce(timeline, output_dir=folder_path, cache_dir=temp_dir)

        # For uniform downstream compatibility, ensure narration.wav mirrors master.wav
        master_path = results.get("master_path")
        narration_path = os.path.join(folder_path, "narration.wav")
        if master_path and os.path.exists(master_path):
            if not os.path.exists(narration_path) or os.path.abspath(master_path) != os.path.abspath(narration_path):
                shutil.copyfile(master_path, narration_path)

        # Save cue_sheet.json
        import json
        cue_json = os.path.join(folder_path, "cue_sheet.json")
        try:
            with open(cue_json, "w", encoding="utf-8") as f:
                json.dump(timeline, f, indent=2)
        except Exception:
            pass

        duration_min = results.get("duration_sec", 0.0) / 60.0
        size_mb = os.path.getsize(master_path) / (1024 * 1024) if master_path and os.path.exists(master_path) else 0.0
        measured_lufs = results.get("lufs", -16.0)

        self.log(f"  [TYPE 2 DRAMA COMPLETE] Stems & Master created: Duration: {duration_min:.2f} min | Master Size: {size_mb:.2f} MB | LUFS: {measured_lufs:.2f}")

        # Clean cache
        shutil.rmtree(temp_dir, ignore_errors=True)
        self._prune_output_folder(folder_path, is_type_2=True)

        return {
            "wav_path": master_path,
            "master_path": master_path,
            "dialogue_path": results.get("dialogue_path"),
            "foley_path": results.get("foley_path"),
            "ambience_path": results.get("ambience_path"),
            "duration_min": duration_min,
            "size_mb": size_mb,
            "lufs": measured_lufs
        }

    @classmethod
    def _clean_type3_text(cls, text: str, sid: int, sinfo: dict) -> str:
        """Preprocesses Type 3 archival text: removes chapter announcements, metadata headers,
        stage directions/pauses, ensures dialogue separation, and appends an official archival sign-off.
        """
        import re
        title = sinfo.get("title", f"Case {400 + sid}")
        m = re.search(r'Case\s+(\d+):\s*(.+)$', title, re.IGNORECASE)
        case_no = m.group(1) if m else str(400 + sid)
        short_title = m.group(2).strip() if m else title

        # Strip markdown and headers
        text = re.sub(r'(?im)^\s*#+\s+.*$', '', text)
        text = re.sub(r'(?im)^\s*\*\*.*?\*\*.*$', '', text)
        text = re.sub(r'(?im)^\s*---+\s*$', '', text)

        # Strip chapter announcements and titles (e.g. Chapter 1: Archival Intake...)
        text = re.sub(r'(?im)^\s*Chapter\s+\d+[:\s\-\–\—].*$', '', text)
        text = re.sub(r'(?im)^\s*Chapter\s+\d+\s*$', '', text)

        # Strip archival metadata headers from beginning of chapters
        text = re.sub(r'(?im)^\s*Restricted\s+[Aa]rchival\s+[Rr]ecording\s+[Hh]eader:?.*$', '', text)
        text = re.sub(r'(?im)^\s*Confidentiality\s+Level:?.*$', '', text)
        text = re.sub(r'(?im)^\s*Case\s+Background:?.*$', '', text)
        text = re.sub(r'(?im)^\s*Initial\s+Emergency\s+Dispatch:?.*$', '', text)

        # Prefer curated date and location from registry, with safe fallbacks
        date_str = sinfo.get("date")
        if not date_str:
            date_m = re.search(r'(?:March|April|May|June|July|August|September|October|November|December|January|February)\s+\d{1,2}(?:st|nd|rd|th)?,\s*\d{4}', text)
            date_str = date_m.group(0) if date_m else f"October {sid}, 1987"

        loc_str = sinfo.get("location")
        if not loc_str:
            loc_str = "Classified DUA Survey Zone"

        # Strip (pause), [pause], and emotion tags - replace with subtle pauses (...)
        text = re.sub(r'(?i)\((?:pause|pause\s+[\d\.]+s?|sighs?|whispers?|gasps?|laughter|groans?)\)', '... ', text)
        text = re.sub(r'(?i)\[(?:pause|pause\s+[\d\.]+s?|sighs?|whispers?|gasps?|laughter|groans?)\]', '... ', text)

        # Ensure speaker turns have distinct paragraph breaks for clear pause gaps
        text = re.sub(r'([.!?\"”\)])\s*([A-Z][A-Za-z\s]{1,25}:\s*[\"“])', r'\1\n\n\2', text)

        # Strip initial timestamp line if at the very start
        text = text.lstrip()
        text = re.sub(r'^(?:March|April|May|June|July|August|September|October|November|December|January|February)\s+\d{1,2}(?:st|nd|rd|th)?,\s*\d{4}[^\n]*\n+', '', text)

        text = text.strip()
        # Ensure all numbers, dates, times, measurements, and identifiers are expanded to spoken words
        text = cls._expand_numbers_to_words(text)

        # Official archival sign-off at the end
        signoff = f"\n\nArchival case record complete. Case {case_no}: {short_title}. Incident recorded {date_str}, {loc_str}. Department of Unlisted Assets, Central Vault Archive. Record sealed."
        text += signoff
        return text

    @classmethod
    def _expand_numbers_to_words(cls, text: str) -> str:
        """Expands numbers, times, dates, years, fractions, ordinals, and Roman numerals
        into natural spoken English words.
        """
        try:
            from num2words import num2words
        except ImportError:
            return text

        import re
        months = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
        decades = {
            '20s': 'twenties', '30s': 'thirties', '40s': 'forties', '50s': 'fifties',
            '60s': 'sixties', '70s': 'seventies', '80s': 'eighties', '90s': 'nineties'
        }
        romans = {
            'II': 'two', 'III': 'three', 'IV': 'four', 'V': 'five', 'VI': 'six',
            'VII': 'seven', 'VIII': 'eight', 'IX': 'nine', 'X': 'ten', 'XI': 'eleven', 'XII': 'twelve'
        }

        # 1. Dates: Month Day, Year
        def _date_repl(m):
            mo, d, yr = m.group(1), int(m.group(2)), int(m.group(3))
            return f"{mo} {num2words(d, to='ordinal')}, {num2words(yr, to='year')}"
        text = re.sub(rf'\b({months})\s+(\d{{1,2}}),\s+(\d{{4}})\b', _date_repl, text)

        # 2. Month Ordinal: March 10th
        def _date_ord(m):
            return f"{m.group(1)} {num2words(int(m.group(2)), to='ordinal')}"
        text = re.sub(rf'\b({months})\s+(\d{{1,2}})(?:st|nd|rd|th)\b', _date_ord, text)

        # 3. Timestamps: HH:MM:SS or HH:MM
        def _time_repl(m):
            h, mn, s = int(m.group(1)), int(m.group(2)), m.group(3)
            h_str = "midnight" if h == 0 and mn == 0 and not s else ("zero" if h == 0 else num2words(h))
            m_str = ("o'clock" if h != 0 and not s else "zero") if mn == 0 else (f"oh-{num2words(mn)}" if mn < 10 else num2words(mn))
            res = f"{h_str} {m_str}"
            if s:
                sec = int(s[1:])
                sec_str = "zero" if sec == 0 else (f"oh-{num2words(sec)}" if sec < 10 else num2words(sec))
                res += f" {sec_str}"
            return res
        text = re.sub(r'\b(\d{1,2}):(\d{2})(:\d{2})?\b', _time_repl, text)

        # 4. Decades
        def _dec_repl(m):
            raw = m.group(1).lower()
            if raw in decades:
                return decades[raw]
            elif len(raw) == 5 and raw.endswith('s'):
                return num2words(int(raw[:4]), to='year') + 's'
            return raw
        text = re.sub(r'\b(\d{2,4}s)\b', _dec_repl, text, flags=re.IGNORECASE)

        # 5. Fractions
        for frac, w in [('1/4', 'one quarter'), ('1/2', 'one half'), ('3/4', 'three quarters'), ('1/3', 'one third'), ('2/3', 'two thirds')]:
            text = re.sub(rf'\b{re.escape(frac)}\b', w, text)

        # 6. Ordinals
        text = re.sub(r'\b(\d+)(?:st|nd|rd|th)\b', lambda m: num2words(int(m.group(1)), to='ordinal'), text)

        # 7. Compound hyphenated units: 30-minute, 50-foot
        text = re.sub(r'\b(\d+)-(minute|hour|foot|feet|meter|second|mile|yard|ton|person|year|day|month)\b',
                      lambda m: f"{num2words(int(m.group(1)))}-{m.group(2)}", text, flags=re.IGNORECASE)

        # 8. Decimals: 3.7 -> three point seven
        text = re.sub(r'\b(\d+)\.(\d+)\b',
                      lambda m: f"{num2words(int(m.group(1)))} point {' '.join([num2words(int(d)) for d in m.group(2)])}", text)

        # 9. Roman numerals (excluding standalone I)
        for rom, w in romans.items():
            text = re.sub(rf'\b{rom}\b', w, text)

        # 10. Designations: Unit 401 -> Unit four-zero-one, Room 104 -> Room one-zero-four
        def _desig_repl(m):
            pfx, num_str = m.group(1), m.group(2)
            if len(num_str) == 3:
                digits = "-".join(['zero' if d == '0' else num2words(int(d)) for d in num_str])
                return f"{pfx} {digits}"
            return f"{pfx} {num2words(int(num_str))}"
        text = re.sub(r'\b(Unit|Room|Cell|Tower|Sub-Basement|Sub-basement|Basement|Shaft|Case|Incident)\s+(\d+)\b',
                      _desig_repl, text, flags=re.IGNORECASE)

        # 11. Standalone / comma-separated numbers: 1,500, 300
        def _num_repl(m):
            raw = m.group(0).replace(',', '')
            val = int(raw)
            if val in [1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]:
                return f"{num2words(val // 100)} hundred"
            elif 1700 <= val <= 2099:
                return num2words(val, to='year')
            return num2words(val)
        text = re.sub(r'\b\d{1,3}(?:,\d{3})+\b|\b\d+\b', _num_repl, text)
        return text

    async def render_type3_audio(self, sid: int, sinfo: dict, full_text: str, folder_path: str) -> dict:
        """Renders Type 3 archival case file audio with low grounded voice, clean speaker pauses,
        removal of chapter announcements and stage directions, and official archival sign-off.
        """
        gender = sinfo.get("gender", "male")
        voice = self.get_voice(gender, sid=sid, preferred_voice=sinfo.get("voice"))
        from .catalog import StoryCatalog
        canonical_name = StoryCatalog.get_audio_filename(sid, sinfo)
        canonical_wav = os.path.join(folder_path, canonical_name)
        legacy_wav = os.path.join(folder_path, "narration.wav")
        temp_dir = os.path.join(REPO_ROOT, "scratch", f"render_cache_type3_{sid}")
        os.makedirs(temp_dir, exist_ok=True)

        self.log(f"  Selected Type 3 archival voice: {voice} (Gender: {gender.upper()}) | Target: {canonical_name}")

        # Preprocess archival text: strip metadata, chapter headers, pauses, add signoff
        cleaned_text = self._clean_type3_text(full_text, sid, sinfo)
        chunks = self._chunk_text(cleaned_text, max_chars=1800)
        self.log(f"  Starting Type 3 TTS rendering: {len(chunks)} chunks using {voice} (lowered pitch -5Hz, rate -10%)...")

        sem = asyncio.Semaphore(3)
        temp_files = [None] * len(chunks)

        async def render_chunk(idx, chunk_text):
            chunk_file = os.path.join(temp_dir, f"chunk_{idx}.mp3")
            if os.path.exists(chunk_file) and os.path.getsize(chunk_file) > 1000:
                try:
                    sf.info(chunk_file)
                    temp_files[idx - 1] = chunk_file
                    return
                except Exception:
                    try:
                        os.remove(chunk_file)
                    except OSError:
                        pass

            max_retries = 6
            for attempt in range(1, max_retries + 1):
                async with sem:
                    try:
                        comm = edge_tts.Communicate(chunk_text, voice, rate="-10%", pitch="-5Hz")
                        await asyncio.wait_for(comm.save(chunk_file), timeout=120.0)
                        if os.path.exists(chunk_file) and os.path.getsize(chunk_file) > 1000:
                            sf.info(chunk_file)
                            temp_files[idx - 1] = chunk_file
                            self.log(f"    [TTS] Chunk {idx}/{len(chunks)} rendered ({os.path.getsize(chunk_file)//1024} KB).")
                            return
                        else:
                            raise IOError("Downloaded chunk file was empty or corrupted.")
                    except Exception as e:
                        self.log(f"    [WARN] Type 3 TTS Chunk {idx}/{len(chunks)} attempt {attempt} failed: {type(e).__name__} ({e}). Retrying in {attempt * 2}s...")
                        if os.path.exists(chunk_file):
                            try:
                                os.remove(chunk_file)
                            except OSError:
                                pass
                        await asyncio.sleep(attempt * 2)

            raise RuntimeError(f"Type 3 TTS Chunk {idx}/{len(chunks)} failed after {max_retries} attempts.")

        try:
            tasks = [render_chunk(idx, chunk_text) for idx, chunk_text in enumerate(chunks, 1)]
            await asyncio.gather(*tasks)
            await asyncio.sleep(1.0)
            self.log(f"  Stitching {len(temp_files)} audio chunks into 48 kHz float32 {canonical_name}...")
            raw_assembled = os.path.join(temp_dir, "raw_assembled_temp.wav")
            # Stream directly to disk to consume minimal RAM
            AudioBuffer.stream_stitch_files(temp_files, raw_assembled, gap_sec=0.65, target_sample_rate=TARGET_SAMPLE_RATE)

            # Broadcast mastering via stream: -16 LUFS integrated, -1 dBTP true peak limiting
            self.log("  Mastering track to EBU R128 (-16 LUFS, -1 dBTP true-peak)...")
            AudioMasteringConsole.master_file_stream(raw_assembled, canonical_wav, target_sample_rate=TARGET_SAMPLE_RATE)

            # Maintain legacy narration.wav link/copy for downstream compatibility
            if os.path.abspath(canonical_wav) != os.path.abspath(legacy_wav):
                try:
                    if os.path.exists(legacy_wav):
                        os.remove(legacy_wav)
                    os.link(canonical_wav, legacy_wav)
                except OSError:
                    shutil.copyfile(canonical_wav, legacy_wav)

            info = sf.info(canonical_wav)
            duration_min = info.duration / 60.0
            size_mb = os.path.getsize(canonical_wav) / (1024 * 1024)

            self.log(f"  [TYPE 3 COMPLETE] Archival track created: Duration: {duration_min:.2f} min | File Size: {size_mb:.2f} MB | LUFS: -16.00")


            self._prune_output_folder(folder_path)

            return {
                "wav_path": canonical_wav,
                "duration_min": duration_min,
                "size_mb": size_mb,
                "voice": voice,
                "lufs": measured_lufs
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def _chunk_text(full_text: str, max_chars: int = 1800) -> list:
        """Splits full text into chunks at paragraph or sentence boundaries <= max_chars."""
        import re

        # Strip chapter announcements, numbers, and titles (e.g. "Chapter 1: The Cheap Lease & The Five Rules")
        full_text = re.sub(r'(?im)^\s*Chapter\s+\d+[:\s\-\–\—].*$', '', full_text)
        full_text = re.sub(r'(?im)^\s*Chapter\s+\d+\s*$', '', full_text)
        # Strip markdown headers, bold headers, and horizontal rules
        full_text = re.sub(r'(?im)^\s*#+\s+.*$', '', full_text)
        full_text = re.sub(r'(?im)^\s*\*\*.*?\*\*.*$', '', full_text)
        full_text = re.sub(r'(?im)^\s*---+\s*$', '', full_text)

        raw_paragraphs = full_text.split("\n\n")
        atoms = []
        for p in raw_paragraphs:
            clean_p = p.strip()
            if not clean_p:
                continue
            if len(clean_p) <= max_chars:
                atoms.append(clean_p)
            else:
                sentences = re.split(r'(?<=[.!?])\s+', clean_p)
                for s in sentences:
                    s_clean = s.strip()
                    if not s_clean:
                        continue
                    if len(s_clean) <= max_chars:
                        atoms.append(s_clean)
                    else:
                        words = s_clean.split(" ")
                        w_curr = []
                        w_len = 0
                        for w in words:
                            if w_len + len(w) + 1 > max_chars and w_curr:
                                atoms.append(" ".join(w_curr))
                                w_curr = [w]
                                w_len = len(w)
                            else:
                                w_curr.append(w)
                                w_len += len(w) + 1
                        if w_curr:
                            atoms.append(" ".join(w_curr))

        chunks = []
        curr = []
        curr_len = 0
        for atom in atoms:
            if curr_len + len(atom) + 2 > max_chars and curr:
                chunks.append("\n\n".join(curr))
                curr = [atom]
                curr_len = len(atom)
            else:
                curr.append(atom)
                curr_len += len(atom) + 2
        if curr:
            chunks.append("\n\n".join(curr))
        return chunks

    @staticmethod
    def _prune_output_folder(folder_path: str, is_type_2: bool = False):
        """Preserves canonical wavs, markdown files, txt files, and json cue sheets."""
        for f in os.listdir(folder_path):
            if f.endswith(".wav") or f.endswith(".md") or f.endswith(".txt") or f.endswith(".json"):
                continue
            fp = os.path.join(folder_path, f)
            try:
                if os.path.isfile(fp):
                    os.remove(fp)
            except OSError:
                pass
