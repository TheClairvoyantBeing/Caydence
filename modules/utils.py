import os
import subprocess
import re


def get_next_serialized_index(base_dir="Theoutput"):
    """Scans base_dir for folders starting with a number and returns the next integer index."""
    if not os.path.exists(base_dir):
        return 1
    max_idx = 0
    for entry in os.listdir(base_dir):
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(full_path):
            match = re.match(r'^(\d+)-', entry)
            if match:
                try:
                    idx = int(match.group(1))
                    if idx > max_idx:
                        max_idx = idx
                except ValueError:
                    pass
    return max_idx + 1

def create_serialized_output_folder(category="horror", name="TheHouse", base_dir="Theoutput"):
    """
    Creates a serialized output folder in 'Theoutput/' formatted as:
    {serialized_number}-{category}-{name} (e.g. 1-horror-TheHouse).
    """
    os.makedirs(base_dir, exist_ok=True)
    next_idx = get_next_serialized_index(base_dir)
    safe_cat = re.sub(r'[^\w-]', '', category).strip().lower() or "horror"
    words = re.findall(r'[a-zA-Z0-9]+', name)
    safe_name = "".join(w.capitalize() for w in words)[:30] or "Story"
    
    folder_name = os.path.join(base_dir, f"{next_idx}-{safe_cat}-{safe_name}")
    os.makedirs(folder_name, exist_ok=True)
    return folder_name

def create_output_folder(topic, category="horror"):
    """
    Creates a serialized output folder in 'Theoutput/' based on topic and category.
    Kept for backwards compatibility with existing pipeline callers.
    """
    return create_serialized_output_folder(category=category, name=topic)

def convert_to_wav(input_path, output_path, sample_rate=48000, channels=2):
    """
    Standardizes input audio to clean studio WAV format (default: 48 kHz stereo float32).
    """
    try:
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-ar", str(sample_rate),
            "-ac", str(channels),
            "-c:a", "pcm_f32le" if sample_rate >= 48000 else "pcm_s16le",
            output_path
        ]
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except Exception as e:
        print(f"[ERROR] FFmpeg conversion failed for {input_path}: {e}")
        return False

def get_audio_duration(path):
    """Helper to extract the duration of an audio file using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return float(result.stdout)
    except Exception:
        return 0.0
