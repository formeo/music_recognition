from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class AudioAnalysis:
    """Audio analysis results."""
    bpm: float = 0.0
    key: str = ""
    energy: float = 0.0
    duration: float = 0.0
    loudness_db: float = 0.0

    def to_comment(self) -> str:
        """Format as ID3 comment."""
        return f"BPM: {self.bpm:.0f} | Key: {self.key} | Energy: {self.energy:.2f}"


class AudioAnalyzer:
    """Analyze audio characteristics using librosa."""

    KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    MODE_NAMES = ['minor', 'major']

    def __init__(self):
        try:
            import librosa
            self.librosa = librosa
        except ImportError:
            raise ImportError("librosa is required: pip install librosa")

    def analyze(self, file_path: str) -> AudioAnalysis:
        """Perform full audio analysis."""
        y, sr = self.librosa.load(file_path, sr=22050, duration=60)  # First 60 sec

        return AudioAnalysis(
            bpm=self._detect_bpm(y, sr),
            key=self._detect_key(y, sr),
            energy=self._calculate_energy(y),
            duration=self.librosa.get_duration(y=y, sr=sr),
            loudness_db=self._calculate_loudness(y),
        )

    def _detect_bpm(self, y, sr) -> float:
        """Detect tempo in BPM."""
        tempo, _ = self.librosa.beat.beat_track(y=y, sr=sr)
        return float(tempo[0]) if hasattr(tempo, '__iter__') else float(tempo)

    def _detect_key(self, y, sr) -> str:
        """Detect musical key."""
        # Compute chromagram
        chroma = self.librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)

        # Find dominant pitch class
        key_idx = int(np.argmax(chroma_mean))

        # Simple major/minor detection based on intervals
        # (more sophisticated methods exist)
        return f"{self.KEY_NAMES[key_idx]}"

    def _calculate_energy(self, y) -> float:
        """Calculate average RMS energy."""
        rms = self.librosa.feature.rms(y=y)
        return float(np.mean(rms))

    def _calculate_loudness(self, y) -> float:
        """Calculate loudness in dB."""
        rms = np.sqrt(np.mean(y ** 2))
        return float(20 * np.log10(rms + 1e-10))