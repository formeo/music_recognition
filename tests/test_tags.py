"""Tag reading/writing across audio formats (real files generated with ffmpeg)."""

from unittest.mock import AsyncMock

import pytest

from music_recognition import MusicRecognizer, TrackInfo

from .test_regressions import SHAZAM_RESPONSE, make_audio, pytestmark  # noqa: F401  (ffmpeg skip marker)

TAGGABLE = ["mp3", "flac", "m4a", "ogg", "opus"]

INFO = TrackInfo(title="Song", artist="Artist", album="Album", year="1999", genre="Electronic", track_number="3")


@pytest.mark.parametrize("ext", TAGGABLE)
def test_write_and_read_back(tmp_path, ext):
    path = str(make_audio(tmp_path / f"t.{ext}"))

    assert MusicRecognizer.write_tags(path, INFO) is True
    assert MusicRecognizer.has_valid_tags(path) is True

    read = MusicRecognizer.read_existing_tags(path)
    assert (read.title, read.artist, read.album, read.year, read.genre, read.track_number) == (
        "Song", "Artist", "Album", "1999", "Electronic", "3"
    )


@pytest.mark.parametrize("ext", TAGGABLE)
def test_existing_tags_kept_without_overwrite(tmp_path, ext):
    path = str(make_audio(tmp_path / f"t.{ext}"))
    MusicRecognizer.write_tags(path, INFO)

    other = TrackInfo(title="Other", artist="Someone")
    assert MusicRecognizer.write_tags(path, other) is False
    assert MusicRecognizer.read_existing_tags(path).title == "Song"

    assert MusicRecognizer.write_tags(path, other, overwrite=True) is True
    assert MusicRecognizer.read_existing_tags(path).title == "Other"


@pytest.mark.parametrize("ext", ["wav", "aac"])
def test_untaggable_formats_skipped_with_warning(tmp_path, ext, caplog):
    path = str(make_audio(tmp_path / f"t.{ext}"))
    assert MusicRecognizer.write_tags(path, INFO) is False
    assert "not supported" in caplog.text


@pytest.mark.asyncio
async def test_tagged_flac_is_skipped_on_second_run(tmp_path):
    make_audio(tmp_path / "t.flac")
    r = MusicRecognizer(delay_between_requests=0, use_cache=False)
    r.shazam.recognize = AsyncMock(return_value=SHAZAM_RESPONSE)

    first = await r.process_directory(str(tmp_path))
    second = await r.process_directory(str(tmp_path))

    assert first.recognized == 1
    assert second.skipped == 1
    assert r.shazam.recognize.call_count == 1
