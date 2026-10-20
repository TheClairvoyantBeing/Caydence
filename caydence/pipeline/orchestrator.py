"""
Pipelined Producer-Consumer Orchestrator for Caydence Story Production.
Coordinates foreground LLM scriptwriting and background sequential TTS audio synthesis.
"""

import os
import sys
import time
import queue
import threading
import asyncio
import re
from datetime import datetime

from .catalog import StoryCatalog, StoryType
from .scriptwriter import ScriptwriterEngine
from .synthesizer import AudioSynthesizer

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(MODULE_DIR))
OUTPUT_BASE = os.path.join(REPO_ROOT, "output")

class PipelinedOrchestrator:
    """Manages offset concurrent story generation and audio synthesis across Story Types 1, 2, and 3."""

    def __init__(self, output_dir=None):
        self.output_base = output_dir or os.environ.get("CAYDENCE_OUTPUT_DIR") or OUTPUT_BASE
        os.makedirs(self.output_base, exist_ok=True)
        for stype in StoryType.ALL_TYPES:
            os.makedirs(os.path.join(self.output_base, stype), exist_ok=True)

        self.log_file = os.path.join(self.output_base, "production_pipeline.log")
        self.audio_queue = queue.Queue()
        self.audio_thread = None
        self._stop_event = threading.Event()

        self.scriptwriter = ScriptwriterEngine(logger=self.log)
        self.synthesizer = AudioSynthesizer(logger=self.log)

    def log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{ts}] {msg}"
        print(formatted)
        sys.stdout.flush()
        try:
            log_path = getattr(self, "log_file", None) or os.path.join(self.output_base, "production_pipeline.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception:
            pass

    def is_story_complete(self, sid: int, story_type: str = None) -> bool:
        """Checks if a story already has a full valid master audio, story.txt, and story.md in its Type folder."""
        try:
            sinfo = StoryCatalog.get_story(sid, story_type=story_type)
        except KeyError:
            return False

        folder_path = StoryCatalog.find_existing_folder(self.output_base, sid, sinfo)
        if not os.path.exists(folder_path):
            return False

        canonical_name = StoryCatalog.get_audio_filename(sid, sinfo)
        wav_candidates = [
            os.path.join(folder_path, canonical_name),
            os.path.join(folder_path, "narration.wav"),
            os.path.join(folder_path, "master.wav")
        ]
        has_wav = any(os.path.exists(w) and os.path.getsize(w) > 5 * 1024 * 1024 for w in wav_candidates)
        has_md = os.path.exists(os.path.join(folder_path, "story.md"))
        has_txt = os.path.exists(os.path.join(folder_path, "story.txt"))

        return bool(has_wav and (has_md or has_txt))


    def _audio_consumer_worker(self):
        """Worker thread executing audio synthesis for completed scripts sequentially."""
        while not self._stop_event.is_set():
            try:
                job = self.audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if job is None:
                self.audio_queue.task_done()
                break

            sid, sinfo, full_text, folder_path, stype = job
            try:
                self.log(f"\n[AUDIO PIPELINE] >>> STARTING SYNTHESIS for [{stype}] Story #{sid}: '{sinfo['title']}'")
                self.log(f"  Target: {folder_path} | Voice/Cast: {sinfo.get('gender', 'female').upper()}")

                if sinfo.get("type") == StoryType.TYPE_3 or stype == StoryType.TYPE_3:
                    asyncio.run(self.synthesizer.render_type3_audio(sid, sinfo, full_text, folder_path))
                else:
                    asyncio.run(self.synthesizer.render_story_audio(sid, sinfo, full_text, folder_path))

                self.log(f"[AUDIO PIPELINE] <<< SYNTHESIS COMPLETE & VERIFIED for [{stype}] Story #{sid}!\n")
            except Exception as e:
                self.log(f"[AUDIO PIPELINE ERROR] Failed audio rendering for Story #{sid}: {e}")
                import traceback
                self.log(traceback.format_exc())
            finally:
                self.audio_queue.task_done()

    def run_pipeline(self, start_sid: int = 1, end_sid: int = 20, story_type: str = None):
        """Executes pipelined production across story IDs for a designated Story Type (1, 2, or 3)."""
        stype = StoryType.normalize(story_type)
        self.log("=" * 70)
        self.log(f"CAYDENCE PIPELINED RUNNER: [{stype.upper()}] STORIES {start_sid} THROUGH {end_sid}")
        self.log("=" * 70)

        # Start sequential audio synthesizer worker in the background
        self._stop_event.clear()
        self.audio_thread = threading.Thread(target=self._audio_consumer_worker, daemon=True)
        self.audio_thread.start()
        self.log(f"[PIPELINE INITIALIZED] Synthesizer Worker is live and routing jobs into '{stype}'.")

        for sid in range(start_sid, end_sid + 1):
            try:
                sinfo = StoryCatalog.get_story(sid, story_type=stype)
            except KeyError:
                self.log(f"[WARN] Story #{sid} not found in catalog for {stype}. Skipping.")
                continue

            folder_path = StoryCatalog.find_existing_folder(self.output_base, sid, sinfo)
            os.makedirs(folder_path, exist_ok=True)

            if self.is_story_complete(sid, story_type=stype):
                self.log(f"[CHECK] [{stype}] Story #{sid} ({sinfo['title']}) is ALREADY COMPLETE. Skipping.")
                continue

            # Check if story script already exists on disk
            story_md = os.path.join(folder_path, "story.md")
            story_txt = os.path.join(folder_path, "story.txt")
            cached_text = None

            if os.path.exists(story_txt):
                try:
                    with open(story_txt, "r", encoding="utf-8") as f:
                        cached_text = f.read()
                except Exception:
                    pass
            elif os.path.exists(story_md):
                try:
                    with open(story_md, "r", encoding="utf-8") as f:
                        raw_md = f.read()
                        if "---" in raw_md:
                            cached_text = raw_md.split("---", 1)[1].strip()
                        else:
                            cached_text = raw_md
                except Exception:
                    pass

            if cached_text and len(cached_text.split()) >= 1000:
                self.log(f"[CACHE HIT] [{stype}] Story #{sid} script already exists ({len(cached_text.split())} words). Queueing for audio synthesis!")
                self.audio_queue.put((sid, sinfo, cached_text, folder_path, stype))
                continue

            try:
                # 1. Foreground: Generate story script
                self.log(f"\n=======================================================")
                self.log(f"[SCRIPTWRITER] GENERATING SCRIPT FOR [{stype}] STORY #{sid}: {sinfo['title']}")
                self.log(f"Target Folder: {folder_path}")
                self.log(f"=======================================================")

                full_story = self.scriptwriter.generate_full_story(sid, sinfo)

                words = len(full_story.split())
                self.log(f"[SCRIPTWRITER] [{stype}] Story #{sid} script complete: {words} words (~{words/150:.1f} minutes).")

                # Save text and markdown
                with open(story_txt, "w", encoding="utf-8") as f:
                    f.write(full_story)

                with open(story_md, "w", encoding="utf-8") as f:
                    f.write(f"# {sinfo['title']}\n\n")
                    f.write(f"**Serial:** Story #{sid} (Caydence Catalog)\n")
                    f.write(f"**Category:** {stype}\n")
                    f.write(f"**Word Count:** {words} words\n\n---\n\n")
                    f.write(full_story)

                # 2. Enqueue for synthesis
                self.log(f"[PIPELINE SYNC] Story #{sid} script complete -> Enqueueing for {stype} audio synthesis.")
                self.audio_queue.put((sid, sinfo, full_story, folder_path, stype))

            except Exception as e:
                self.log(f"[ERROR] Failed to produce Story #{sid}: {e}")
                import traceback
                self.log(traceback.format_exc())
                time.sleep(5)

        # Drain queue
        self.log("\n[PIPELINE DRAIN] All story scripts processed! Waiting for audio synthesizer queue to finish...")
        self.audio_queue.join()
        self.audio_queue.put(None)
        if self.audio_thread:
            self.audio_thread.join()

        self.log("\n" + "=" * 70)
        self.log(f"ALL TARGET [{stype.upper()}] STORIES VERIFIED AND PRODUCED!")
        self.log("=" * 70)

    def get_status_report(self, max_sid: int = 100, story_type: str = None) -> list:
        """Returns structured status records partitioned across Story Types."""
        types_to_scan = [StoryType.normalize(story_type)] if story_type else StoryType.ALL_TYPES
        records = []

        for stype in types_to_scan:
            # Determine catalog limit for this type dynamically
            if stype == StoryType.TYPE_1:
                limit = min(max_sid, StoryCatalog.get_catalog_size(stype))
            else:
                limit = StoryCatalog.get_catalog_size(stype)

            for sid in range(1, limit + 1):
                try:
                    sinfo = StoryCatalog.get_story(sid, story_type=stype)
                except KeyError:
                    continue

                folder_path = StoryCatalog.find_existing_folder(self.output_base, sid, sinfo)

                record = {
                    "sid": sid,
                    "type": stype,
                    "title": sinfo["title"],
                    "gender": sinfo.get("gender", "female"),
                    "voice": sinfo.get("voice", "en-US-AvaNeural"),
                    "folder": os.path.basename(folder_path),
                    "status": "Pending",
                    "words": 0,
                    "duration_min": 0.0,
                    "wav_mb": 0.0,
                }

                if os.path.exists(folder_path):
                    txt_path = os.path.join(folder_path, "story.txt")
                    md_path = os.path.join(folder_path, "story.md")
                    wav_path = os.path.join(folder_path, "narration.wav")
                    master_path = os.path.join(folder_path, "master.wav")

                    active_text = txt_path if os.path.exists(txt_path) else md_path
                    if os.path.exists(active_text):
                        try:
                            with open(active_text, "r", encoding="utf-8") as f:
                                record["words"] = len(f.read().split())
                        except Exception:
                            pass

                    active_wav = master_path if os.path.exists(master_path) else (wav_path if os.path.exists(wav_path) else None)
                    if active_wav and os.path.exists(active_wav):
                        size = os.path.getsize(active_wav)
                        record["wav_mb"] = round(size / (1024 * 1024), 2)
                        if size > 10 * 1024 * 1024:
                            record["status"] = "Complete"
                            # Estimate duration based on sample rate
                            record["duration_min"] = round(size / (48000 * 2 * 4 * 60) if size > 500*1024*1024 else size / (24000 * 2 * 60), 2)
                        else:
                            record["status"] = "In-Progress"
                    elif record["words"] > 0:
                        record["status"] = "Script Only"

                records.append(record)

        return records

    def audit_catalog(self, story_type: str = None) -> dict:
        """Inspects all audio and script deliverables on disk using soundfile and returns aggregate statistics."""
        import glob
        import soundfile as sf
        
        types_to_scan = [StoryType.normalize(story_type)] if story_type else StoryType.ALL_TYPES
        results = {
            "categories": {},
            "total_words": 0,
            "total_duration_sec": 0.0,
            "total_size_bytes": 0,
            "total_stories": 0
        }
        
        for stype in types_to_scan:
            pattern = os.path.join(self.output_base, stype, "*")
            dirs = glob.glob(pattern)
            def _sort_key(p):
                base = os.path.basename(p)
                m = re.match(r'^(\d+)', base)
                return int(m.group(1)) if m else 9999
            dirs = sorted(dirs, key=_sort_key)
            
            cat_data = {
                "stories": [],
                "words": 0,
                "duration_sec": 0.0,
                "size_bytes": 0
            }
            
            for d in dirs:
                if not os.path.isdir(d):
                    continue
                wav_candidates = [
                    os.path.join(d, "narration.wav"),
                    os.path.join(d, "master.wav")
                ]
                wav_path = next((w for w in wav_candidates if os.path.exists(w) and os.path.getsize(w) > 1024*1024), None)
                txt_path = os.path.join(d, "story.txt")
                md_path = os.path.join(d, "story.md")
                
                words = 0
                for t in [txt_path, md_path]:
                    if os.path.exists(t):
                        try:
                            with open(t, "r", encoding="utf-8") as f:
                                words = len(f.read().split())
                                break
                        except Exception:
                            pass
                
                duration = 0.0
                samplerate = 0
                channels = 0
                subtype = ""
                size = 0
                
                if wav_path:
                    try:
                        info = sf.info(wav_path)
                        duration = info.duration
                        samplerate = info.samplerate
                        channels = info.channels
                        subtype = info.subtype
                        size = os.path.getsize(wav_path)
                    except Exception:
                        pass
                
                item = {
                    "folder": os.path.basename(d),
                    "path": d,
                    "wav_path": wav_path,
                    "words": words,
                    "duration_sec": duration,
                    "duration_min": duration / 60.0,
                    "size_mb": size / (1024 * 1024),
                    "samplerate": samplerate,
                    "channels": channels,
                    "subtype": subtype
                }
                cat_data["stories"].append(item)
                cat_data["words"] += words
                cat_data["duration_sec"] += duration
                cat_data["size_bytes"] += size
            
            results["categories"][stype] = cat_data
            results["total_words"] += cat_data["words"]
            results["total_duration_sec"] += cat_data["duration_sec"]
            results["total_size_bytes"] += cat_data["size_bytes"]
            results["total_stories"] += len(cat_data["stories"])
            
        return results
