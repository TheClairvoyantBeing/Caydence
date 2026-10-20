"""
Caydence Unified Command Line Interface.
Provides entry points for:
  - `caydence`: General interactive / single story and TTS generation.
  - `caydence-pipeline`: Industrial batch & long-form catalog orchestrator.
"""

import os
import sys
import argparse

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .utils import create_output_folder, convert_to_wav
from .story_engine import StoryEngine
from .audio_engine import AudioEngine
from .voice_engine import VoiceEngine
from .pipeline import StoryCatalog, StoryType, PipelinedOrchestrator


def cleanup_empty_folders(root):
    """Recursively removes empty directories starting from root."""
    for dir_path, dir_names, file_names in os.walk(root, topdown=False):
        if not dir_names and not file_names:
            try:
                os.rmdir(dir_path)
            except OSError:
                pass


def select_mode():
    """Interactive CLI menu for operational mode."""
    print("\n=== CAYDENCE -- MODE SELECT ===")
    print("1. Story only     (generate script, save story.txt)")
    print("2. TTS only       (narrate an existing story.txt)")
    print("3. Auto           (story -> TTS, full pipeline)")
    choice = input("Select (1/2/3): ").strip()
    return {"1": "story", "2": "tts", "3": "auto"}.get(choice, "auto")


def select_voice(voice_engine):
    """Handles selection of a reference voice."""
    print("\n--- VOICE SELECTION ---")
    print("1. Curated Narrator Archetypes (from voice_samples/)")
    print("2. Your own voice sample (mp3/wav/m4a)")
    voice_choice = input("Select (1/2): ").strip()
    
    if voice_choice == "1":
        available = voice_engine.list_available_voices()
        if not available:
            print("[INFO] No custom samples found in voice_samples/ yet.")
            print("[INFO] You can drop any 5-15s audio clip into voice_samples/ or provide a path below.")
            sample_path = input("Path to voice sample file: ").strip().replace('"', '')
            if not os.path.exists(sample_path):
                print(f"[ERROR] Not found: {sample_path}")
                sys.exit(1)
            return voice_engine.prepare_voice_sample(sample_path)
            
        categories = list(available.keys())
        for idx, cat in enumerate(categories, 1):
            print(f"  {idx}. {cat} ({len(available[cat])} sample(s))")
        cat_idx = int(input("Category: ").strip()) - 1
        selected_cat = categories[cat_idx]
        
        voices = available[selected_cat]
        for idx, voice in enumerate(voices, 1):
            print(f"  {idx}. {voice}")
        voice_idx = int(input("Voice: ").strip()) - 1
        reference_path = os.path.join(voice_engine.sample_dir, selected_cat, voices[voice_idx])
    else:
        sample_path = input("Path to voice sample: ").strip().replace('"', '')
        if not os.path.exists(sample_path):
            print(f"[ERROR] Not found: {sample_path}")
            sys.exit(1)
            
        ext = os.path.splitext(sample_path)[1].lower()
        if ext in [".mp4", ".mp3", ".m4a", ".ogg", ".flac"]:
            temp_wav = "temp_reference.wav"
            if convert_to_wav(sample_path, temp_wav):
                reference_path = temp_wav
            else:
                sys.exit(1)
        else:
            reference_path = sample_path
            
    return reference_path


def build_caydence_parser():
    """Builds CLI argument parser for `caydence`."""
    parser = argparse.ArgumentParser(
        prog="caydence",
        description="Caydence — Cinematic Audio Drama & Industrial Narration Engine"
    )
    parser.add_argument("--mode", choices=["story", "tts", "auto"], help="Operational mode")
    parser.add_argument("--topic", help="Story topic / gist")
    parser.add_argument("--duration", default="50+", help="Estimated duration in minutes (e.g. 50+, 60, 90+)")
    parser.add_argument(
        "--style", 
        default="reddit_internet", 
        help="Storytelling framework (reddit_internet, horror_scary, true_crime, history_bio, documentary, fiction_dramatized, mafia_werewolf)"
    )
    parser.add_argument("--story-file", help="Path to existing story.txt for TTS mode")
    parser.add_argument("--voice-sample", help="Path to reference voice audio sample")
    return parser


def main():
    """Main CLI entrypoint for `caydence` command."""
    parser = build_caydence_parser()
    args = parser.parse_args()

    print("=" * 60)
    print("      CAYDENCE -- CINEMATIC AUDIO DRAMA ENGINE")
    print("=" * 60)

    mode = args.mode or select_mode()

    if mode == "tts":
        story_file = args.story_file or input("\nPath to existing story.txt: ").strip().replace('"', '')
        if not os.path.exists(story_file):
            print(f"[ERROR] Not found: {story_file}")
            sys.exit(1)
        with open(story_file, "r", encoding="utf-8") as f:
            story_text = f.read()
        
        topic = os.path.basename(os.path.dirname(story_file)) or "tts_session"
        
        voice_engine = VoiceEngine()
        default_ref = "voice_samples/1_Mr_Nightmare_Grounded_Baritone/narrator_22k.wav"
        if args.voice_sample:
            reference_path = args.voice_sample
        elif os.path.exists(default_ref) and not sys.stdin.isatty():
            reference_path = default_ref
        else:
            reference_path = select_voice(voice_engine)
        try:
            audio_engine = AudioEngine()
        except Exception as e:
            print(e)
            sys.exit(1)
        
        session_root = os.path.dirname(story_file) if os.path.dirname(story_file) else create_output_folder(topic)
        output_audio = os.path.join(session_root, "narration.wav")
        audio_engine.generate_narration(story_text, reference_path, output_audio)
        
        if os.path.exists("temp_reference.wav"):
            os.remove("temp_reference.wav")
        cleanup_empty_folders(".")
        return

    if args.topic:
        topic = args.topic
        duration_str = args.duration
        style = args.style
    else:
        print("\n--- STORY CONFIG (YouTube Storytelling Frameworks) ---")
        topic = input("Story idea / gist: ").strip()
        print("\nStyle Archetype:")
        print("1. Reddit / Internet Stories (One-Shot, 50+ min)")
        print("2. Horror & Scary Stories   (Multi-Series: Part 1, Part 2..., 50+ min/part)")
        print("3. True Crime & Mystery     (Multi-Series, 50+ min/part)")
        print("4. History & Documentary    (Multi-Series, 50+ min/part)")
        print("5. Fiction / Mafia / Werewolf (Multi-Series / Foolproof, 90+ min)")
        print("6. Mr. Nightmare Realism    (Multi-Series, 50+ min/part)")
        style_choice = input("Style (1-6, default 1): ").strip()
        style_map = {
            "1": "reddit_internet",
            "2": "horror_scary",
            "3": "true_crime",
            "4": "documentary",
            "5": "mafia_werewolf",
            "6": "mr_nightmare"
        }
        style = style_map.get(style_choice, "reddit_internet")

        default_dur = "90+" if style in ["mafia_werewolf", "fiction_dramatized"] else "50+"
        print(f"\n1. 50+ min (Standard minimum)  2. 60 min  3. 90+ min (Fiction minimum)  4. Custom (default: {default_dur})")
        dur_choice = input("Duration (1/2/3/4): ").strip()
        duration_map = {"1": "50+", "2": "60", "3": "90+"}
        duration_str = input("Minutes: ").strip() if dur_choice == "4" else duration_map.get(dur_choice, default_dur)

    try:
        story_engine = StoryEngine()
    except Exception as e:
        print(e)
        sys.exit(1)

    cat_name = "reddit" if "reddit" in style else ("horror" if "horror" in style or "nightmare" in style or "creepypasta" in style else style)
    session_root = create_output_folder(topic, category=cat_name)
    story_txt = os.path.join(session_root, "story.txt")
    story_md = os.path.join(session_root, "story.md")

    story_text = story_engine.generate_story(topic, duration_str, style=style)
    if not story_text:
        print("[ERROR] Story generation failed.")
        sys.exit(1)

    with open(story_txt, "w", encoding="utf-8") as f:
        f.write(story_text)

    first_line = story_text.strip().split("\n")[0].strip("#* ")
    with open(story_md, "w", encoding="utf-8") as f:
        f.write(f"# {first_line or topic}\n\n**Category:** {style}\n\n---\n\n{story_text}\n")
    print(f"\n[INFO] Story saved ->\n  * {story_txt}\n  * {story_md}")

    if mode == "story":
        print("\n[INFO] Story-only mode complete. Run TTS separately with mode 2.")
        cleanup_empty_folders(".")
        return

    voice_engine = VoiceEngine()
    default_ref = "voice_samples/1_Mr_Nightmare_Grounded_Baritone/narrator_22k.wav"
    if args.voice_sample:
        reference_path = args.voice_sample
    elif os.path.exists(default_ref) and args.topic:
        reference_path = default_ref
    else:
        reference_path = select_voice(voice_engine)

    try:
        audio_engine = AudioEngine()
    except Exception as e:
        print(e)
        sys.exit(1)

    output_audio = os.path.join(session_root, "narration.wav")
    audio_engine.generate_narration(story_text, reference_path, output_audio)

    if os.path.exists("temp_reference.wav"):
        os.remove("temp_reference.wav")
    print(f"\n[DONE] All outputs created in -> {os.path.abspath(session_root)}")
    cleanup_empty_folders(".")


def print_status_table(records, filter_type=None):
    title_suffix = f" [{filter_type.upper()}]" if filter_type else ""
    print("\n" + "=" * 115)
    print(f"CAYDENCE MASTER PRODUCTION STATUS (CATALOG OVERVIEW){title_suffix}")
    print("=" * 115)
    fmt = "{:<4} {:<8} {:<38} {:<8} {:<12} {:<10} {:<10} {:<12}"
    print(fmt.format("ID", "Type", "Title", "Gender", "Status", "Words", "WAV (MB)", "Voice/Cast"))
    print("-" * 115)

    completed_by_type = {StoryType.TYPE_1: 0, StoryType.TYPE_2: 0, StoryType.TYPE_3: 0}
    total_by_type = {StoryType.TYPE_1: 0, StoryType.TYPE_2: 0, StoryType.TYPE_3: 0}

    for r in records:
        st = r.get("type", StoryType.TYPE_1)
        total_by_type[st] = total_by_type.get(st, 0) + 1
        if r["status"] == "Complete":
            completed_by_type[st] = completed_by_type.get(st, 0) + 1

        voice_short = r["voice"].replace("en-US-", "").replace("Neural", "")
        title_truncated = (r["title"][:35] + "...") if len(r["title"]) > 38 else r["title"]
        print(fmt.format(
            r["sid"],
            st,
            title_truncated,
            r["gender"].capitalize(),
            r["status"],
            f"{r['words']:,}" if r['words'] else "-",
            f"{r['wav_mb']} MB" if r['wav_mb'] else "-",
            voice_short
        ))
    print("=" * 115)
    summary_parts = []
    for t in StoryType.ALL_TYPES:
        if total_by_type.get(t, 0) > 0:
            summary_parts.append(f"{t}: {completed_by_type.get(t, 0)}/{total_by_type[t]} Complete")
    print(" | ".join(summary_parts) + "\n")


def print_audit_report(audit_data, filter_type=None):
    title_suffix = f" [{filter_type.upper()}]" if filter_type else ""
    print("\n" + "=" * 115)
    print(f"CAYDENCE PHYSICAL MASTER AUDIO DISK AUDIT{title_suffix}")
    print("=" * 115)
    fmt = "{:<4} {:<8} {:<34} {:<10} {:<12} {:<10} {:<12} {:<12}"
    print(fmt.format("ID", "Type", "Title", "Duration", "SampleRate", "Channels", "File (MB)", "Status"))
    print("-" * 115)

    valid_count = 0
    total_dur_sec = 0.0

    for r in audit_data:
        if r["status"] == "OK":
            valid_count += 1
            total_dur_sec += r["duration_sec"]
            dur_fmt = f"{int(r['duration_sec'] // 60):02d}:{int(r['duration_sec'] % 60):02d}"
            sr_fmt = f"{r['sample_rate']} Hz"
            ch_fmt = "Stereo (2)" if r["channels"] == 2 else ("Mono (1)" if r["channels"] == 1 else str(r["channels"]))
            mb_fmt = f"{r['size_mb']} MB"
            stat_fmt = "[VERIFIED]"
        else:
            dur_fmt = "-"
            sr_fmt = "-"
            ch_fmt = "-"
            mb_fmt = "-"
            stat_fmt = f"[{r['status']}]"

        title_truncated = (r["title"][:31] + "...") if len(r["title"]) > 34 else r["title"]
        print(fmt.format(
            r["sid"],
            r["type"],
            title_truncated,
            dur_fmt,
            sr_fmt,
            ch_fmt,
            mb_fmt,
            stat_fmt
        ))

    print("=" * 115)
    total_hrs = total_dur_sec / 3600.0
    print(f"SUMMARY: {valid_count}/{len(audit_data)} Audio Files Physically Verified | Total Duration: {total_hrs:.2f} Hours\n")


def pipeline_main():
    """CLI entrypoint for `caydence-pipeline` command."""
    parser = argparse.ArgumentParser(
        prog="caydence-pipeline",
        description="Caydence Industrial Long-Form Audio Generator (Type 1, Type 2, Type 3)"
    )
    parser.add_argument("--status", action="store_true", help="Display status table across catalog story types")
    parser.add_argument("--audit", action="store_true", help="Run physical disk audit across all produced master tracks using soundfile")
    parser.add_argument("--type", type=str, default=None, help="Story production type: 1 (Reddit Confessions), 2 (Survival Rules), 3 (DUA Case Files)")
    parser.add_argument("--start", type=int, default=1, help="Starting Story ID (default: 1)")
    parser.add_argument("--end", type=int, default=None, help="Ending Story ID (default: full catalog size for selected type)")
    parser.add_argument("--story", type=int, default=None, help="Produce a specific single Story ID")
    parser.add_argument("--max-catalog", type=int, default=100, help="Catalog range to inspect for status (default: 100)")

    args = parser.parse_args()
    orchestrator = PipelinedOrchestrator()

    normalized_type = StoryType.normalize(args.type) if args.type else None

    if args.audit:
        audit_data = orchestrator.audit_catalog(story_type=normalized_type)
        print_audit_report(audit_data, filter_type=normalized_type)
        return

    if args.status:
        records = orchestrator.get_status_report(max_sid=args.max_catalog, story_type=normalized_type)
        print_status_table(records, filter_type=normalized_type)
        return

    target_type = normalized_type or StoryType.TYPE_1
    catalog_limit = StoryCatalog.get_catalog_size(target_type)

    if args.story is not None:
        start_sid = args.story
        end_sid = args.story
    else:
        start_sid = args.start
        end_sid = min(args.end, catalog_limit) if args.end is not None else catalog_limit

    print(f"\n[CLI] Starting pipelined execution for [{target_type}] Story #{start_sid} through Story #{end_sid} (Catalog Max: {catalog_limit})...")
    orchestrator.run_pipeline(start_sid=start_sid, end_sid=end_sid, story_type=target_type)


if __name__ == "__main__":
    main()

