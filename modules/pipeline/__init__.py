"""
Caydence Industrial Long-Form Audio Pipeline Package.
Provides end-to-end 50+ min multi-chapter story generation and pipelined neural voice synthesis.
"""

from .catalog import StoryCatalog, StoryType, STORY_REGISTRY, TYPE_2_REGISTRY, TYPE_3_REGISTRY
from .scriptwriter import ScriptwriterEngine
from .synthesizer import AudioSynthesizer
from .orchestrator import PipelinedOrchestrator

__all__ = [
    "StoryType",
    "StoryCatalog",
    "STORY_REGISTRY",
    "TYPE_2_REGISTRY",
    "TYPE_3_REGISTRY",
    "ScriptwriterEngine",
    "AudioSynthesizer",
    "PipelinedOrchestrator",
]
