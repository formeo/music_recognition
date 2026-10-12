"""
Regression tests for file-safety bugs (rename, conversion, tags, cache).

These tests generate real audio files with ffmpeg and mock only the Shazam call.
"""

import shutil
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from mutagen.easyid3 import EasyID3

from music_recognition import MusicRecognizer
from music_recognition.cache import RecognitionCache
from music_recognition.models import TrackInfo

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is required")

SHAZAM_RESPONSE = {
    "track": {
        "title": "Song",
        "subtitle": "Artist",
        "key": "42",
        "genres": {"primary": "Electronic"},
        "hub": {"options": [{"caption": "OPEN IN", "listcaption": "Open in Apple Music"}]},
        "sections": [{"type": "SONG", "metadata": [{"title": "Album", "text": "Album"}]}],
    }
}

NO_ALBUM_RESPONSE = {"track": {"title": "Song", "subtitle": "Artist", "key": "42"}}


def make_audio(path: Path) -> Path:
    subprocess.run(
        ["ffmpeg", "-loglevel", "quiet", "-f", "lavfi", "-i", "sine=f=440:d=2", str(path)],
        check=True,
    )
    return path


def listing(directory: Path) -> list:
    return sorted(str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file())


def snapshot(directory: Path) -> dict:
    return {str(p.relative_to(directory)): p.read_bytes() for p in directory.rglob("*") if p.is_file()}


@pytest.fixture
def recognizer():
    r = MusicRecognizer(delay_between_requests=0, use_cache=False)
    r.shazam.recognize = AsyncMock(return_value=SHAZAM_RESPONSE)
    return r


# ---------- rename / move ----------

@pytest.mark.asyncio
async def test_default_run_keeps_filename(recognizer, tmp_path):
    make_audio(tmp_path / "track01.mp3")
    await recognizer.process_directory(str(tmp_path))
    assert listing(tmp_path) == ["track01.mp3"]


@pytest.mark.asyncio
async def test_forced_rerun_with_rename_is_noop(recognizer, tmp_path):
    make_audio(tmp_path / "track01.mp3")
    await recognizer.process_directory(str(tmp_path), rename=True)
    assert listing(tmp_path) == ["Artist - Song.mp3"]

    await recognizer.process_directory(str(tmp_path), rename=True, skip_recognized=False)
    assert listing(tmp_path) == ["Artist - Song.mp3"]


@pytest.mark.asyncio
async def test_second_run_changes_nothing(recognizer, tmp_path):
    make_audio(tmp_path / "a.mp3")
    make_audio(tmp_path / "b.flac")
    await recognizer.process_directory(str(tmp_path), rename=True)
    before = snapshot(tmp_path)

    await recognizer.process_directory(str(tmp_path), rename=True)
    assert snapshot(tmp_path) == before


# ---------- conversion ----------

@pytest.mark.asyncio
async def test_default_run_does_not_convert_or_delete(recognizer, tmp_path):
    make_audio(tmp_path / "orig.flac")
    await recognizer.process_directory(str(tmp_path))
    assert listing(tmp_path) == ["orig.flac"]


@pytest.mark.asyncio
async def test_convert_keeps_source_by_default(recognizer, tmp_path):
    make_audio(tmp_path / "orig.flac")
    await recognizer.process_directory(str(tmp_path), convert_formats=True)
    assert listing(tmp_path) == ["orig.flac", "orig.mp3"]


@pytest.mark.asyncio
async def test_convert_deletes_source_only_when_asked(recognizer, tmp_path):
    make_audio(tmp_path / "orig.flac")
    await recognizer.process_directory(str(tmp_path), convert_formats=True, delete_source=True)
    assert listing(tmp_path) == ["orig.mp3"]


# ---------- extension ----------

@pytest.mark.asyncio
async def test_rename_keeps_real_extension(recognizer, tmp_path):
    make_audio(tmp_path / "x.flac")
    await recognizer.process_directory(str(tmp_path), rename=True)
    assert listing(tmp_path) == ["Artist - Song.flac"]


@pytest.mark.asyncio
async def test_rename_template_without_extension(recognizer, tmp_path):
    make_audio(tmp_path / "x.m4a")
    await recognizer.process_directory(str(tmp_path), rename=True, rename_template="{artist} - {title}")
    assert listing(tmp_path) == ["Artist - Song.m4a"]


@pytest.mark.asyncio
async def test_non_mp3_tags_skipped_with_warning(recognizer, tmp_path, caplog):
    path = make_audio(tmp_path / "x.flac")
    assert MusicRecognizer.write_tags(str(path), TrackInfo(title="Song", artist="Artist")) is False
    assert "not supported" in caplog.text


# ---------- metadata ----------

@pytest.mark.asyncio
async def test_genre_comes_from_genres_primary(recognizer, tmp_path):
    path = make_audio(tmp_path / "t.mp3")
    await recognizer.process_directory(str(tmp_path))
    assert EasyID3(str(path))["genre"] == ["Electronic"]


@pytest.mark.asyncio
async def test_missing_album_is_not_invented(recognizer, tmp_path):
    recognizer.shazam.recognize = AsyncMock(return_value=NO_ALBUM_RESPONSE)
    source = tmp_path / "src"
    source.mkdir()
    make_audio(source / "t.mp3")
    out = tmp_path / "out"

    await recognizer.process_directory(str(source), output_dir=str(out), organize=True)

    assert listing(out) == ["Artist/t.mp3"]
    assert "album" not in EasyID3(str(out / "Artist" / "t.mp3"))


# ---------- cache ----------

@pytest.mark.asyncio
async def test_cache_hit_returns_full_track_info(tmp_path):
    path = make_audio(tmp_path / "t.mp3")
    r = MusicRecognizer(delay_between_requests=0, cache_path=str(tmp_path / "cache.db"))
    r.shazam.recognize = AsyncMock(return_value=SHAZAM_RESPONSE)

    first = await r.recognize_file(str(path))
    second = await r.recognize_file(str(path))

    assert second == first
    assert r.shazam.recognize.call_count == 1


def test_cache_reads_legacy_entries(tmp_path):
    path = make_audio(tmp_path / "t.mp3")
    cache = RecognitionCache(str(tmp_path / "cache.db"))
    legacy = '{"title": "Song", "artist": "Artist", "album": "A", "year": "", "genre": "", "recognized": true}'
    with cache._connect() as conn:
        conn.execute(
            "INSERT INTO cache (audio_hash, track_info) VALUES (?, ?)",
            (cache._hash_audio(str(path)), legacy),
        )

    info = cache.get(str(path))
    assert info.title == "Song" and info.artist == "Artist"


@pytest.mark.asyncio
async def test_dry_run_then_real_run_does_not_fail(tmp_path):
    make_audio(tmp_path / "t.mp3")
    r = MusicRecognizer(delay_between_requests=0, cache_path=str(tmp_path.parent / f"{tmp_path.name}.db"))
    r.shazam.recognize = AsyncMock(return_value=SHAZAM_RESPONSE)

    await r.process_directory(str(tmp_path), dry_run=True)
    stats = await r.process_directory(str(tmp_path))

    assert stats.failed == 0
    assert stats.recognized == 1
