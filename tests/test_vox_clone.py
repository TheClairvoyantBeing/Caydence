"""Automated Test Suite for Caydence.

Validates TTS text sanitization (removing tags, edits, formatting),
output directory generation, duration heuristics, and watermarker patching.
"""

import os
import sys
import shutil
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.audio_engine import clean_text_for_tts, _NullWatermarker
from modules.utils import create_output_folder, get_audio_duration, convert_to_wav


class TestVoxCloneEngine(unittest.TestCase):
    """Tests the Caydence text normalization and utility functions."""

    def test_clean_text_for_tts_paralinguistic_tags(self):
        """Ensure bracketed paralinguistic cues are removed so they aren't spoken literally."""
        raw_text = "I heard a noise outside [gasp] and then total silence [sigh]."
        cleaned = clean_text_for_tts(raw_text)
        self.assertEqual(cleaned, "I heard a noise outside and then total silence.")

    def test_clean_text_for_tts_edits_and_formatting(self):
        """Ensure Reddit [EDIT] headers and markdown asterisks are stripped."""
        raw_text = """
        **Never** enter the basement at 3:00 AM.
        [EDIT 1]: My door just unlocked itself.
        [EDIT]: The power is out.
        </think>
        """
        cleaned = clean_text_for_tts(raw_text)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("[EDIT 1]", cleaned)
        self.assertNotIn("[EDIT]", cleaned)
        self.assertNotIn("</think>", cleaned)
        self.assertIn("Never enter the basement", cleaned)
        self.assertIn("My door just unlocked itself", cleaned)

    def test_output_folder_sanitization(self):
        """Ensure output directory name is sanitized and created."""
        temp_base = tempfile.mkdtemp(prefix="vox_test_")
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_base)
            topic = 'Haunted Forest: What Lurks in Blackwood? [100% Real]'
            folder = create_output_folder(topic)
            self.assertTrue(os.path.isdir(folder))
            self.assertNotIn("?", folder)
            self.assertNotIn(":", folder)
            self.assertNotIn("[", folder)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_base, ignore_errors=True)

    def test_null_watermarker_passthrough(self):
        """Ensure fallback watermarker returns waveform untouched."""
        watermarker = _NullWatermarker()
        fake_wav = [0.1, 0.2, 0.3]
        result = watermarker.apply_watermark(fake_wav, sample_rate=22050)
        self.assertEqual(result, fake_wav)

    def test_missing_audio_duration_returns_zero(self):
        """Ensure missing audio files gracefully return 0.0 duration."""
        duration = get_audio_duration("non_existent_audio_file.wav")
        self.assertEqual(duration, 0.0)

    def test_convert_to_wav_and_duration_probing(self):
        """Ensure convert_to_wav normalizes audio to 22050Hz mono and duration probes accurately."""
        import shutil
        import subprocess
        if not shutil.which("ffmpeg"):
            self.skipTest("ffmpeg binary not installed on host system")
        temp_dir = tempfile.mkdtemp(prefix="vox_audio_test_")
        try:
            in_audio = os.path.join(temp_dir, "input.wav")
            out_wav = os.path.join(temp_dir, "output_converted.wav")
            # Generate 1.0 second test audio using ffmpeg
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", in_audio]
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0 and os.path.exists(in_audio):
                success = convert_to_wav(in_audio, out_wav)
                self.assertTrue(success)
                self.assertTrue(os.path.exists(out_wav))
                dur = get_audio_duration(out_wav)
                self.assertGreater(dur, 0.8)
                self.assertLess(dur, 1.2)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_chunk_text_splits_and_cleans(self):
        """Ensure chunk_text strips tags and splits long passages properly."""
        from modules.audio_engine import chunk_text
        text = "Hello world! [laugh] This is a test. And here is a third sentence."
        chunks = chunk_text(text, max_chars=50)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertNotIn("[laugh]", chunk)
            self.assertLessEqual(len(chunk), 50)

    def test_cleanup_empty_folders(self):
        """Ensure cleanup_empty_folders removes empty directories but preserves files."""
        from main import cleanup_empty_folders
        temp_dir = tempfile.mkdtemp(prefix="vox_cleanup_test_")
        try:
            empty_sub = os.path.join(temp_dir, "empty_dir", "nested_empty")
            os.makedirs(empty_sub, exist_ok=True)
            non_empty = os.path.join(temp_dir, "has_file")
            os.makedirs(non_empty, exist_ok=True)
            with open(os.path.join(non_empty, "keep.txt"), "w") as f:
                f.write("content")
            
            cleanup_empty_folders(temp_dir)
            self.assertFalse(os.path.exists(empty_sub))
            self.assertTrue(os.path.exists(os.path.join(non_empty, "keep.txt")))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_story_engine_missing_key_raises_error(self):
        """Ensure StoryEngine raises ValueError when no NVIDIA_API_KEY is available."""
        from modules.story_engine import StoryEngine
        old_key = os.environ.get("NVIDIA_API_KEY")
        if "NVIDIA_API_KEY" in os.environ:
            del os.environ["NVIDIA_API_KEY"]
        try:
            with self.assertRaises(ValueError):
                StoryEngine(api_key=None)
        finally:
            if old_key is not None:
                os.environ["NVIDIA_API_KEY"] = old_key

    def test_voice_engine_category_mappings(self):
        """Ensure VoiceEngine initializes category directory mappings properly."""
        from modules.voice_engine import VoiceEngine
        ve = VoiceEngine(sample_dir="tests/test_samples")
        self.assertIn("narrative_story", ve.category_map)
        self.assertEqual(ve.category_map["narrative_story"], "4_Narrative_Storyteller")

    def test_cli_parser_options(self):
        """Ensure CLI parser accepts mode, duration, style, and topic flags."""
        from main import build_parser
        parser = build_parser()
        args = parser.parse_args([
            "--mode", "story",
            "--topic", "Cabin in the Woods",
            "--duration", "45",
            "--style", "mr_nightmare"
        ])
        self.assertEqual(args.mode, "story")
        self.assertEqual(args.topic, "Cabin in the Woods")
        self.assertEqual(args.duration, "45")
        self.assertEqual(args.style, "mr_nightmare")



if __name__ == "__main__":
    unittest.main()
