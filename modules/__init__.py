"""
Caydence Core Audio Drama & Storytelling Modules Package
"""
__version__ = "1.0.0"

from .audio_engine import AudioEngine, AudioBuffer, AudioMasteringConsole
from .story_engine import StoryEngine
from .voice_engine import VoiceEngine, VoiceProvider, CharacterVoiceManager, AgeFX, FemaleVoiceBenchmark
from .sound_design import SoundDesignEngine
from .spatial_mix import SpatialMixer
from .cue_sheet import CueSheetParser, AudioDramaProducer
from .pipeline import (
    StoryType,
    StoryCatalog,
    STORY_REGISTRY,
    TYPE_2_REGISTRY,
    ScriptwriterEngine,
    AudioSynthesizer,
    PipelinedOrchestrator
)

__all__ = [
    "AudioEngine",
    "AudioBuffer",
    "AudioMasteringConsole",
    "StoryEngine",
    "VoiceEngine",
    "VoiceProvider",
    "CharacterVoiceManager",
    "AgeFX",
    "FemaleVoiceBenchmark",
    "SoundDesignEngine",
    "SpatialMixer",
    "CueSheetParser",
    "AudioDramaProducer",
    "StoryType",
    "StoryCatalog",
    "STORY_REGISTRY",
    "TYPE_2_REGISTRY",
    "ScriptwriterEngine",
    "AudioSynthesizer",
    "PipelinedOrchestrator",
]
