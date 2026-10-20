import unittest


class TestPackaging(unittest.TestCase):
    def test_caydence_version(self):
        import modules
        self.assertEqual(modules.__version__, "1.0.0")

    def test_caydence_imports(self):
        from modules import (
            AudioEngine,
            AudioBuffer,
            AudioMasteringConsole,
            StoryEngine,
            VoiceEngine,
            SoundDesignEngine,
            SpatialMixer,
            CueSheetParser,
            AudioDramaProducer,
            StoryCatalog,
            PipelinedOrchestrator,
        )
        self.assertIsNotNone(AudioEngine)
        self.assertIsNotNone(AudioBuffer)
        self.assertIsNotNone(AudioMasteringConsole)
        self.assertIsNotNone(StoryEngine)
        self.assertIsNotNone(VoiceEngine)
        self.assertIsNotNone(SoundDesignEngine)
        self.assertIsNotNone(SpatialMixer)
        self.assertIsNotNone(CueSheetParser)
        self.assertIsNotNone(AudioDramaProducer)
        self.assertIsNotNone(StoryCatalog)
        self.assertIsNotNone(PipelinedOrchestrator)

    def test_cli_parser(self):
        from modules.cli import build_caydence_parser
        parser = build_caydence_parser()
        args = parser.parse_args(["--mode", "auto", "--topic", "test story"])
        self.assertEqual(args.mode, "auto")
        self.assertEqual(args.topic, "test story")


if __name__ == "__main__":
    unittest.main()
