"""
Music Recognition - Identify, tag, rename and organize your music collection.

Usage:
    from music_recognition import MusicRecognizer
    
    recognizer = MusicRecognizer()
    stats = await recognizer.process_directory("/music", rename=True)
"""

from .core import (
    MusicRecognizer,
    TrackInfo,
    ProcessingResult,
    ProcessingStats,
    recognize_and_tag,
    setup_logging,
    __version__,
    __author__,
)

__all__ = [
    'MusicRecognizer',
    'TrackInfo',
    'ProcessingResult',
    'ProcessingStats',
    'recognize_and_tag',
    'setup_logging',
    '__version__',
    '__author__',
]
