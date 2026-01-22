from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TrackInfo:
    """Recognized track metadata."""
    title: str = "Unknown"
    artist: str = "Unknown"
    album: str = "Unknown Album"
    year: str = ""
    genre: str = ""
    track_number: str = ""
    cover_url: str = ""
    shazam_id: str = ""
    confidence: float = 0.0

    @property
    def is_recognized(self) -> bool:
        """Check if track was successfully recognized."""
        return self.title != "Unknown" and self.artist != "Unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "year": self.year,
            "genre": self.genre,
            "recognized": self.is_recognized,
        }
