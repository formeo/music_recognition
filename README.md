# music-recognition-tool

[![PyPI](https://img.shields.io/pypi/v/music-recognition-tool.svg)](https://pypi.org/project/music-recognition-tool/)
[![Python](https://img.shields.io/pypi/pyversions/music-recognition-tool.svg)](https://pypi.org/project/music-recognition-tool/)
[![Tests](https://github.com/formeo/music_recognition/actions/workflows/python-package.yml/badge.svg)](https://github.com/formeo/music_recognition/actions/workflows/python-package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A command-line tool and Python library for batch identification of audio files. It recognizes tracks with Shazam, writes the results to file tags, and optionally renames files and sorts them into an `Artist/Album` directory structure.

Typical use: a large collection of files named `Track01.mp3`, vinyl rips, or anything a media server (Plex, Jellyfin) lists as "Unknown Artist".

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [How processing works](#how-processing-works)
- [Command-line reference](#command-line-reference)
- [Filename templates](#filename-templates)
- [Supported formats](#supported-formats)
- [Reports](#reports)
- [Python API](#python-api)
- [Safety](#safety)
- [Limitations](#limitations)
- [Development](#development)
- [Support](#support)
- [License](#license)

## Features

- Track recognition through Shazam, with retries and a configurable number of concurrent requests.
- Tag writing for MP3 (ID3), FLAC, OGG and Opus (Vorbis comments), and M4A (MP4 atoms): title, artist, album, year, genre.
- Renaming from a template such as `{artist} - {title}`; the original file extension is always preserved.
- Moving files into `<output>/<Artist>/<Album>/`.
- Files that already have title and artist tags are skipped, and a repeated run over the same directory changes nothing.
- Dry-run mode that reports planned changes without touching any file.
- JSON and CSV reports.
- Optional conversion to MP3 that keeps the source file unless deletion is requested explicitly.

## Requirements

- Python 3.10 or later.
- FFmpeg. Required to recognize M4A, Opus, AAC and WMA files and for `--convert`. MP3, FLAC, OGG and WAV are recognized without it, but installing FFmpeg is recommended.

```bash
# Debian / Ubuntu
sudo apt install ffmpeg
# macOS
brew install ffmpeg
# Windows
winget install ffmpeg
```

## Installation

```bash
pip install music-recognition-tool
```

This installs the `music-recognize` command. To install from source:

```bash
git clone https://github.com/formeo/music_recognition.git
cd music_recognition
pip install .
```

## Quick start

Preview the changes first, then apply them:

```bash
music-recognize ~/Music/unsorted --rename --dry-run
music-recognize ~/Music/unsorted --rename
```

Recognize, tag and move files into an `Artist/Album` tree:

```bash
music-recognize ~/Music/unsorted --rename --organize -o ~/Music/sorted
```

Write a report without moving files:

```bash
music-recognize ~/Music/unsorted -o report.json
```

## How processing works

For each supported file found recursively under the given path:

1. **Skip check.** A file whose tags already contain a title and an artist is skipped. `--force` disables this check.
2. **Conversion** (only with `--convert`). Non-MP3 files are converted to MP3 at 320 kbit/s next to the source. The source is kept unless `--delete-source` is given.
3. **Recognition.** The file is sent to Shazam. Failed requests are retried twice with a growing delay.
4. **Tagging.** Tags are written unless `--no-tag` is given. Existing tags are left unchanged unless `--overwrite` is given.
5. **Renaming and moving.** With `--rename`, the file name is built from the template. With `-o DIR`, the file is moved to `DIR`, or with `--organize` to `DIR/<Artist>/<Album>/` (`DIR/<Artist>/` when the album is unknown). If the target name is taken by another file, a suffix ` (1)`, ` (2)`, … is added. A file that is already at its target path is not touched.

Up to `--concurrent` files are recognized at the same time. Recognition results are cached in `~/.music_recognition/cache.db`.

## Command-line reference

```
music-recognize PATH [options]
```

`PATH` is a file or a directory. Directories are scanned recursively.

| Option | Default | Description |
|---|---|---|
| `-o`, `--output PATH` | — | Output directory for moved files. If `PATH` ends in `.json` or `.csv`, a report is written instead (directory mode only). |
| `--rename` | off | Rename files using `--template`. |
| `--template TPL` | `{artist} - {title}.mp3` | Filename template; see [Filename templates](#filename-templates). |
| `--organize` | off | Move files into `<output>/<Artist>/<Album>/`. Requires `-o DIR`; has no effect without it. |
| `--no-tag` | — | Do not write tags. Tags are written by default. |
| `--overwrite` | off | Replace existing tags. Also processes files that would otherwise be skipped. |
| `-f`, `--force` | off | Process files that already have title and artist tags. Their tags are kept unless `--overwrite` is also given. |
| `--convert` | off | Convert non-MP3 files to MP3, keeping the source (directory mode only). |
| `--delete-source` | off | With `--convert`: delete the source file after a successful conversion. |
| `-c`, `--concurrent N` | `5` | Maximum number of simultaneous Shazam requests. |
| `--delay SEC` | `0.5` | Pause after each request, per concurrent slot. |
| `-n`, `--dry-run` | off | Report planned changes without modifying files. |
| `-v`, `--verbose` | off | Debug logging and per-file results. |
| `-q`, `--quiet` | off | Warnings and errors only. |
| `--version` | — | Print the version and exit. |

**Exit codes:** `0` if every file was processed without failure (for a single file: it was recognized); `1` if at least one file failed, the path does not exist, or a single file was skipped or not recognized; `130` if interrupted.

## Filename templates

| Placeholder | Value | When missing |
|---|---|---|
| `{artist}` | Artist | — |
| `{title}` | Track title | — |
| `{album}` | Album | `Unknown` |
| `{year}` | Release year | `Unknown` |
| `{genre}` | Primary genre | `Unknown` |
| `{track}` | Track number | `00` (Shazam does not return track numbers) |

- The file keeps its own extension. A trailing audio extension in the template (such as `.mp3`) is replaced by the real one, so `{artist} - {title}` and `{artist} - {title}.mp3` both rename `song.flac` to `Artist - Title.flac`.
- A `/` in the template creates subdirectories, for example `{artist}/{album}/{title}`.
- In placeholder values, the characters `< > : " / \ | ? *` and control characters are replaced with `_`. Leading and trailing spaces and dots are removed, and values are truncated to 200 characters.

## Supported formats

| Format | Recognition | Tags | Needs FFmpeg |
|---|---|---|---|
| MP3 | yes | ID3 | no |
| FLAC | yes | Vorbis comments | no |
| OGG Vorbis | yes | Vorbis comments | no |
| Opus | yes | Vorbis comments | yes |
| M4A | yes | MP4 atoms | yes |
| WAV | yes | not written | no |
| AAC | yes | not written | yes |
| WMA | yes | not written | yes |

Files whose tags are not written are still recognized, renamed and moved. Use `--convert` if MP3 output with tags is preferred.

## Reports

Reports are written in directory mode with `-o report.json` or `-o report.csv`.

- **JSON** contains summary counters (`total`, `processed`, `recognized`, `failed`, `skipped`, `success_rate`, `duration_seconds`) and one entry per file with its original path, final path, status, error and recognized metadata.
- **CSV** contains one row per file: `original_path`, `final_path`, `status`, `artist`, `title`, `album`, `error`.

Because `-o` accepts a single value, a report and an output directory cannot be produced in the same run.

## Python API

The API is asynchronous.

```python
import asyncio
from music_recognition import MusicRecognizer


async def main() -> None:
    recognizer = MusicRecognizer(
        max_concurrent=5,             # simultaneous Shazam requests
        delay_between_requests=0.5,   # pause after each request, per slot
        retry_attempts=2,             # retries after the first attempt
        use_cache=True,
        cache_path=None,              # default: ~/.music_recognition/cache.db
    )

    stats = await recognizer.process_directory(
        source_dir="/music/unsorted",
        output_dir="/music/sorted",
        write_tags=True,
        rename=True,
        rename_template="{artist} - {title}",
        organize=True,
        overwrite_tags=False,
        skip_recognized=True,
        convert_formats=False,
        delete_source=False,
        dry_run=False,
        progress_callback=lambda done, total, result: print(f"{done}/{total} {result.status}"),
    )

    print(f"{stats.recognized}/{stats.processed} recognized, {stats.failed} failed")


asyncio.run(main())
```

- `process_file(file_path, ...)` processes a single file with the same options, except conversion. It returns a `ProcessingResult`.
- `recognize_file(file_path)` only recognizes a file and returns a `TrackInfo`.
- `recognize_and_tag(path, rename=False, organize=False, output_dir=None)` is a shortcut for a file or a directory with default settings.

`ProcessingStats` exposes `total`, `processed`, `recognized`, `failed`, `skipped`, `success_rate`, `duration_seconds`, `results` and `to_dict()`.

## Safety

- Run with `--dry-run` first, and use a copy of the collection for the first real run.
- Changes are not journaled and cannot be undone automatically. A wrong match from Shazam is written to tags and file names as is.
- With `-o DIR`, files are **moved**, not copied.
- No file is deleted unless `--convert --delete-source` is given.

## Limitations

- Recognition uses [ShazamIO](https://github.com/shazamio/ShazamIO), an unofficial client for Shazam's private API. The API may change or rate-limit requests without notice. If requests start failing, lower `--concurrent` or increase `--delay`.
- Matches are not verified. Short, noisy or live recordings may be misidentified.
- Shazam returns limited metadata: no track numbers, and the album of a track is sometimes a single or a compilation.
- Running `--convert` again over the same directory creates another MP3 for each source file it keeps.

## Development

```bash
git clone https://github.com/formeo/music_recognition.git
cd music_recognition
pip install -e ".[dev]"
pytest
```

Tests that operate on real audio files require FFmpeg and are skipped without it. Shazam is mocked in tests; no network access is needed.

Changes are listed in [CHANGELOG.md](CHANGELOG.md).

## Support

If the tool saves you time, you can support its development on [Boosty](https://boosty.to/formeo).

## License

[MIT](LICENSE). Built on [ShazamIO](https://github.com/shazamio/ShazamIO), [Mutagen](https://github.com/quodlibet/mutagen) and [pydub](https://github.com/jiaaro/pydub).
