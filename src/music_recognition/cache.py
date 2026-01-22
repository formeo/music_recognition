# В начало файла
import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from music_recognition import TrackInfo


class RecognitionCache:
    """Cache for recognition results to avoid duplicate API calls."""

    def __init__(self, db_path: str = "~/.music_recognition/cache.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    audio_hash TEXT PRIMARY KEY,
                    track_info TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON cache(created_at)
            """)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def get(self, file_path: str) -> Optional[TrackInfo]:
        """Get cached result by file hash."""
        audio_hash = self._hash_audio(file_path)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT track_info FROM cache WHERE audio_hash = ?",
                (audio_hash,)
            ).fetchone()

            if row:
                import json
                data = json.loads(row[0])
                return TrackInfo(**data)
        return None

    def set(self, file_path: str, info: TrackInfo):
        """Cache recognition result."""
        import json
        audio_hash = self._hash_audio(file_path)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (audio_hash, track_info) VALUES (?, ?)",
                (audio_hash, json.dumps(info.to_dict()))
            )

    def clear(self, older_than_days: int = 30):
        """Remove old cache entries."""
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM cache WHERE created_at < datetime('now', ?)",
                (f'-{older_than_days} days',)
            )

    @staticmethod
    def _hash_audio(file_path: str, chunk_size: int = 1024 * 1024) -> str:
        """Hash first ~1MB of audio file (enough for fingerprint)."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            hasher.update(f.read(chunk_size))
        return hasher.hexdigest()