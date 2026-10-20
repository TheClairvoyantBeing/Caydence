# main.py
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import argparse
from caydence.utils import create_output_folder, convert_to_wav
from caydence.story_engine import StoryEngine
from caydence.audio_engine import AudioEngine
from caydence.voice_engine import VoiceEngine

def cleanup_empty_folders(root):
    """
    Recursively removes empty directories starting from the root.
    I added this because the dynamic output generation can sometimes leave 
    orphan directories if a session is aborted early.
    """
    for dir_path, dir_names, file_names in os.walk(root, topdown=False):
        if not dir_names and not file_names:
            try:
                os.rmdir(dir_path)
            except OSError:
                pass

def select_mode():
    """
    Interactive CLI menu for selecting the operational mode.
    I kept this simple but effective:
    1. Story only: Just the LLM part (useful for drafting).
    2. TTS only: Just the narration (if you have a finished script).
    3. Auto: The full 'Caydence' experience.
    """
    print("\n=== CAYDENCE -- MODE SELECT ===")
    print("1. Story only     (generate script, save story.txt)")
    print("2. TTS only       (narrate an existing story.txt)")
    print("3. Auto           (story -> TTS, full pipeline)")
    choice = input("Select (1/2/3): ").strip()
    return {"1": "story", "2": "tts", "3": "auto"}.get(choice, "auto")

def select_voice(voice_engine):
    """
    Handles the logic for selecting a reference voice.
    Supports local narrator archetypes or a user-provided audio file.
    Note: If a user provides an mp3/m4a, we convert it to 22k mono wav 
    on the fly to satisfy the TTS engine requirements.
    """
    print("\n--- VOICE SELECTION ---")
    print("1. Curated Narrator Archetypes (from voice_samples/)")
    print("2. Your own voice sample (mp3/wav/m4a)")
    voice_choice = input("Select (1/2): ").strip()
    reference_path = ""
    
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

def build_parser():
    """Builds CLI argument parser for automated and scripted runs."""
    parser = argparse.ArgumentParser(
        description="Caydence — YouTube Horror & Mystery Storytelling + Voice Cloning Pipeline"
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
    """
    Main entry point for Caydence. 
    Supports three modes:
    1. Story only: Generates a horror story script based on a gist.
    2. TTS only: Narrates an existing story.txt file using a voice clone.
    3. Auto: Full end-to-end pipeline (Story -> Narration).
    """
    print("=" * 60)
    print("      CAYDENCE -- YOUTUBE STORYTELLING & TTS PIPELINE")
    print("=" * 60)

    parser = build_parser()
    args = parser.parse_args()

    mode = args.mode or select_mode()

    # Mode 2: TTS-only (requires an existing text file)
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

    # Mode 1 & 3: Require story parameters
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

    # Step 1: Generate the story text
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

    # Step 2: Auto Mode continues to TTS Narration
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

if __name__ == "__main__":
    main()