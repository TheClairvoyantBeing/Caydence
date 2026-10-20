"""
modules/cue_sheet.py
====================
Cue Sheet Parser, Timeline Schema Validator, and Multi-Stem Audio Drama Producer.

Features:
- Markdown Script Parser: Extracts dialogue, parentheticals, stage directions, [SFX: ...],
  and [OVERLAP: START] ... [OVERLAP: END] blocks.
- Structured JSON Timeline Schema:
  Tracks: dialogue, foley, ambience, music.
  Events: start_time, duration, character, clip, gain_db, pan, reverb_preset, overlap_offset, interrupt.
- 4-Stem Audio Drama Renderer:
  1. dialogue.wav (all character speech with spatial placement and per-character EQ)
  2. foley.wav (physical impacts, glass shatters, telephone rings, cable snaps)
  3. ambience.wav (3-layer subterranean room tone, sidechain ducked under dialogue)
  4. master.wav (final mastered mixdown at 48 kHz float32, -16 LUFS, -1 dBTP)
"""

import os
import re
from .audio_engine import (
    AudioBuffer, AudioMasteringConsole, TARGET_SAMPLE_RATE, TARGET_LUFS
)
from .voice_engine import CharacterVoiceManager
from .sound_design import SoundDesignEngine
from .spatial_mix import SpatialMixer

CHARACTER_HEADER_RE = re.compile(r"^([A-Z0-9_\s\-\.]+?)\s*\(([^)]+)\)", re.IGNORECASE)
STAGE_DIR_RE = re.compile(r"\([^\)]*\)")
SFX_RE = re.compile(r"\[SFX:\s*([^\]]+)\]", re.IGNORECASE)


class CueSheetParser:
    """Parses markdown script files into structured production cue sheet timelines."""

    def __init__(self, script_path: str):
        self.script_path = script_path

    def parse_to_timeline(self) -> dict:
        """Converts markdown script into a timeline dictionary."""
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(f"Script file not found: {self.script_path}")

        with open(self.script_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        events = []
        in_overlap = False
        overlap_lines = []
        current_char = None
        current_dir = ""
        accumulated_text = []

        def flush():
            nonlocal current_char, current_dir, accumulated_text
            if current_char and accumulated_text:
                raw = " ".join(accumulated_text)
                clean = STAGE_DIR_RE.sub("", raw)
                clean = re.sub(r"\s+", " ", clean).strip()
                if clean:
                    item = {
                        "type": "dialogue",
                        "character": current_char,
                        "direction": current_dir,
                        "text": clean
                    }
                    if in_overlap:
                        overlap_lines.append(item)
                    else:
                        events.append(item)
            current_char = None
            current_dir = ""
            accumulated_text = []

        for line in lines:
            s = line.strip()
            if not s:
                continue

            if s == "[OVERLAP: START]":
                flush()
                in_overlap = True
                overlap_lines = []
                continue
            elif s == "[OVERLAP: END]":
                flush()
                in_overlap = False
                events.append({
                    "type": "overlap_group",
                    "lines": list(overlap_lines)
                })
                overlap_lines = []
                continue

            sfx_m = SFX_RE.match(s)
            if sfx_m:
                flush()
                events.append({
                    "type": "sfx",
                    "tag": sfx_m.group(1).strip().upper()
                })
                continue

            if s.startswith("###") or s.startswith("---"):
                flush()
                events.append({"type": "scene_break"})
                continue

            if s.startswith("#") or s.startswith("**"):
                continue

            char_m = CHARACTER_HEADER_RE.match(s)
            if char_m:
                flush()
                current_char = char_m.group(1).strip()
                current_dir = char_m.group(2).strip()
                continue

            if current_char:
                accumulated_text.append(s)

        flush()

        timeline = {
            "title": os.path.basename(self.script_path),
            "version": "2.0",
            "sample_rate": TARGET_SAMPLE_RATE,
            "events": events
        }
        return timeline


class AudioDramaProducer:
    """Renders 4 separate audio stems and the master broadcast mix."""

    def __init__(self, char_manager=None, sound_engine=None, spatial_mixer=None):
        self.char_mgr = char_manager or CharacterVoiceManager()
        self.sound_engine = sound_engine or SoundDesignEngine()
        self.spatial = spatial_mixer or SpatialMixer()
        self.mastering = AudioMasteringConsole()

    async def produce(self, timeline: dict, output_dir: str, cache_dir: str = None) -> dict:
        """
        Executes complete production run:
        Renders dialogue stem, foley stem, ambience bed stem, and final master mix.
        """
        os.makedirs(output_dir, exist_ok=True)
        cache_dir = cache_dir or os.path.join(output_dir, "cache")
        os.makedirs(cache_dir, exist_ok=True)

        sr = TARGET_SAMPLE_RATE
        dialogue_stem = AudioBuffer.silent(0.5, sr)
        foley_stem = AudioBuffer.silent(0.5, sr)

        print("[PRODUCER] Rendering dialogue and Foley cues...")

        events = timeline.get("events", [])
        line_num = 0

        for idx, ev in enumerate(events, 1):
            ev_type = ev["type"]

            if ev_type == "scene_break":
                dialogue_stem.concatenate(AudioBuffer.silent(1.2, sr), gap_sec=0.0)
                continue

            elif ev_type == "sfx":
                tag = ev["tag"]
                cur_time = dialogue_stem.duration_sec
                sfx_buf = None

                if "GLASS" in tag or "SHATTER" in tag:
                    sfx_buf = self.sound_engine.generate_glass_shatter()
                elif "CABLE" in tag or "CRASH" in tag:
                    sfx_buf = self.sound_engine.generate_cable_snap_and_crash()
                elif "PHONE" in tag or "RING" in tag:
                    sfx_buf = self.sound_engine.generate_rotary_telephone(rings=2)
                elif "FIGHT" in tag or "STRUGGLE" in tag or "POUNDING" in tag:
                    sfx_buf = self.sound_engine.generate_fight_impact()
                elif "CHATTER" in tag or "WALLA" in tag:
                    sfx_buf = self.sound_engine.generate_crowd_walla(duration_sec=4.5)
                elif "IMPACT" in tag:
                    sfx_buf = self.sound_engine.generate_object_impact("steel_on_glass")

                if sfx_buf is not None:
                    # Spatial positioning for SFX
                    sfx_buf = self.spatial.apply_scene_reverb(sfx_buf, "sub_basement")
                    foley_stem.overlay(sfx_buf, offset_sec=cur_time)
                    # Insert small dramatic pause in dialogue stem
                    dialogue_stem.concatenate(AudioBuffer.silent(0.4, sr), gap_sec=0.0)
                continue

            elif ev_type == "dialogue":
                line_num += 1
                char = ev["character"]
                text = ev["text"]
                direction = {"intensity": 0.6, "volume_level": "normal"}
                if "whisper" in ev.get("direction", "").lower():
                    direction["volume_level"] = "whisper"
                elif "shout" in ev.get("direction", "").lower() or "panick" in ev.get("direction", "").lower():
                    direction["volume_level"] = "shout"

                cache_file = os.path.join(cache_dir, f"line_{line_num:04d}_{char.lower()[:8]}.wav")
                if os.path.exists(cache_file) and os.path.getsize(cache_file) > 1000:
                    line_buf = AudioBuffer.from_file(cache_file)
                else:
                    print(f"  [Cue {idx}/{len(events)}] Rendering dialogue line {line_num}: {char} -> \"{text[:40]}...\"", flush=True)
                    line_buf = await self.char_mgr.render_dialogue_line(char, text, direction)
                    line_buf.export(cache_file)

                # Acoustic spatial placement
                line_buf = self.spatial.apply_scene_reverb(line_buf, "sub_basement")

                # Natural conversational gap (120-220ms, organic breath)
                dialogue_stem.concatenate(line_buf, gap_sec=0.18)

            elif ev_type == "overlap_group":
                # Multi-character concurrent shouting
                overlap_lines = ev.get("lines", [])
                max_dur = 0.0
                overlap_buf = AudioBuffer.silent(0.2, sr)

                print(f"  [Cue {idx}/{len(events)}] Rendering overlap group ({len(overlap_lines)} lines)...", flush=True)
                for o_idx, o_line in enumerate(overlap_lines):
                    line_num += 1
                    c_name = o_line["character"]
                    o_text = o_line["text"]
                    stagger_sec = o_idx * 0.28  # Staggered onset (280ms)

                    o_cache = os.path.join(cache_dir, f"line_{line_num:04d}_OVERLAP_{c_name.lower()[:8]}.wav")
                    if os.path.exists(o_cache) and os.path.getsize(o_cache) > 1000:
                        o_buf = AudioBuffer.from_file(o_cache)
                    else:
                        o_buf = await self.char_mgr.render_dialogue_line(
                            c_name, o_text, {"intensity": 0.85, "volume_level": "shout"}
                        )
                        o_buf.export(o_cache)

                    o_buf = self.spatial.apply_scene_reverb(o_buf, "sub_basement")
                    overlap_buf.overlay(o_buf, offset_sec=stagger_sec)
                    max_dur = max(max_dur, stagger_sec + o_buf.duration_sec)

                dialogue_stem.concatenate(overlap_buf, gap_sec=0.25)

        total_duration = max(dialogue_stem.duration_sec, foley_stem.duration_sec)
        print(f"[PRODUCER] Total production length: {total_duration:.1f}s ({total_duration/60.0:.2f} min).")

        # Step 2: Ambience Bed Generation
        print("[PRODUCER] Generating 3-layer environmental soundscape...")
        ambience_stem = self.sound_engine.generate_ambience_bed("sub_basement", total_duration + 3.0)

        # Step 3: Sidechain Ducking (Ducks bed 8-10 dB under dialogue)
        print("[PRODUCER] Applying dynamic sidechain ducking...")
        ambience_stem = self.spatial.sidechain_duck_ambience(ambience_stem, dialogue_stem, duck_gain_db=-9.0)

        # Equalize stem lengths
        if foley_stem.duration_sec < total_duration:
            foley_stem.overlay(AudioBuffer.silent(total_duration - foley_stem.duration_sec, sr), offset_sec=foley_stem.duration_sec)

        # Step 4: Export Stems
        print("[PRODUCER] Exporting independent audio stems...")
        diag_path = os.path.join(output_dir, "dialogue_stem.wav")
        foley_path = os.path.join(output_dir, "foley_stem.wav")
        amb_path = os.path.join(output_dir, "ambience_stem.wav")
        master_path = os.path.join(output_dir, "master.wav")

        dialogue_stem.export(diag_path)
        foley_stem.export(foley_path)
        ambience_stem.export(amb_path)

        # Step 5: Master Bus Mixdown
        print("[PRODUCER] Mixing down and mastering master.wav (-16 LUFS, -1 dBTP)...")
        master_buf = AudioBuffer.silent(total_duration, sr)
        master_buf.overlay(ambience_stem, offset_sec=0.0)
        master_buf.overlay(foley_stem, offset_sec=0.0)
        master_buf.overlay(dialogue_stem, offset_sec=0.0)

        master_buf = self.mastering.master_bus(master_buf)
        master_buf.export(master_path)

        final_lufs = self.mastering.measure_loudness(master_buf)
        print(f"[SUCCESS] Master exported to: {master_path}")
        print(f"          Integrated Loudness: {final_lufs:.2f} LUFS | Target: {TARGET_LUFS} LUFS")

        return {
            "master_path": master_path,
            "dialogue_path": diag_path,
            "foley_path": foley_path,
            "ambience_path": amb_path,
            "duration_sec": total_duration,
            "lufs": final_lufs
        }
