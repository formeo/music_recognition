# src/music_recognition/__init__.py
"""Music Recognition - Identify, tag, rename and organize music files."""

__author__ = "formeo"

from .core import (
    __version__,
    MusicRecognizer,
    TrackInfo,
    ProcessingResult,
    ProcessingStats,
    recognize_and_tag,
    setup_logging,
)

__all__ = [
    "MusicRecognizer",
    "TrackInfo", 
    "ProcessingResult",
    "ProcessingStats",
    "recognize_and_tag",
    "setup_logging",
    "__version__",
]