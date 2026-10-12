"""Concurrent directory processing: bounded parallelism, no lost files on name collisions."""

import asyncio

import pytest

from music_recognition import MusicRecognizer

from .test_regressions import SHAZAM_RESPONSE, listing, make_audio, pytestmark  # noqa: F401  (ffmpeg skip marker)


class FakeShazam:
    """Records how many recognitions run at the same time; finishes them out of order."""

    def __init__(self):
        self.in_flight = 0
        self.max_in_flight = 0
        self.calls = 0

    async def recognize(self, file_path):
        self.calls += 1
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        await asyncio.sleep(0.01 * (self.calls % 3 + 1))
        self.in_flight -= 1
        return SHAZAM_RESPONSE


def make_recognizer(max_concurrent):
    r = MusicRecognizer(max_concurrent=max_concurrent, delay_between_requests=0, use_cache=False)
    r.shazam = FakeShazam()
    return r


@pytest.mark.asyncio
async def test_requests_run_in_parallel_up_to_limit(tmp_path):
    for i in range(6):
        make_audio(tmp_path / f"{i}.mp3")
    r = make_recognizer(max_concurrent=3)

    stats = await r.process_directory(str(tmp_path), write_tags=False)

    assert r.shazam.max_in_flight == 3
    assert stats.recognized == 6


@pytest.mark.asyncio
async def test_same_track_from_many_files_loses_nothing(tmp_path):
    for i in range(4):
        make_audio(tmp_path / f"{i}.mp3")
    r = make_recognizer(max_concurrent=4)

    await r.process_directory(str(tmp_path), rename=True)

    assert listing(tmp_path) == [
        "Artist - Song (1).mp3",
        "Artist - Song (2).mp3",
        "Artist - Song (3).mp3",
        "Artist - Song.mp3",
    ]


@pytest.mark.asyncio
async def test_progress_reports_each_file_once_in_order(tmp_path):
    for i in range(5):
        make_audio(tmp_path / f"{i}.mp3")
    r = make_recognizer(max_concurrent=5)
    calls = []

    await r.process_directory(
        str(tmp_path), write_tags=False, progress_callback=lambda cur, total, res: calls.append((cur, total))
    )

    assert calls == [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5)]


@pytest.mark.asyncio
async def test_progress_reaches_total_when_conversion_fails(tmp_path):
    make_audio(tmp_path / "ok.mp3")
    (tmp_path / "broken.flac").write_bytes(b"not audio")
    r = make_recognizer(max_concurrent=2)
    calls = []

    stats = await r.process_directory(
        str(tmp_path), convert_formats=True, write_tags=False,
        progress_callback=lambda cur, total, res: calls.append((cur, total)),
    )

    assert calls == [(1, 2), (2, 2)]
    assert stats.failed == 1
