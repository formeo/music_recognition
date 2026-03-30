# 🎵 Music Recognition

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/music-recognition-tool.svg)](https://pypi.org/project/music-recognition-tool/)
[![Tests](https://github.com/formeo/music_recognition/actions/workflows/python-package.yml/badge.svg)](https://github.com/formeo/music_recognition/actions)
[![PyPI Downloads](https://static.pepy.tech/badge/music-recognition-tool/month)](https://pepy.tech/projects/music-recognition-tool)
![Stars](https://img.shields.io/github/stars/formeo/music_recognition)

**Bulk music identification and tagging tool** — bring order to your chaotic music collection.

Automatically identify unknown music files using Shazam, write ID3 tags, rename files, and organize into Artist/Album folders.

## ✨ Features

- 🔍 **Identify tracks** via Shazam API
- 📝 **Write ID3 tags** — title, artist, album, year, genre
- 📁 **Rename files** — customizable templates like `{artist} - {title}.mp3`
- 🗂️ **Organize** — automatic Artist/Album folder structure
- ⚡ **Async processing** — concurrent requests with rate limiting
- 🔄 **Format conversion** — WAV, FLAC, M4A, OGG → MP3
- 📊 **Export reports** — JSON/CSV for processed files
- 🛡️ **Safe** — dry-run mode to preview changes

## 🚀 Quick Start

### Installation

```bash
# From source
git clone https://github.com/formeo/music_recognition.git
cd music_recognition
pip install -e .

# Or install dependencies only
pip install -r requirements.txt
```

### Requirements

- Python 3.9+
- FFmpeg (for audio conversion)

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
```

### Basic Usage

```bash
# Recognize and tag all files in a directory
music-recognize /path/to/music

# Also rename files to "Artist - Title.mp3"
music-recognize /path/to/music --rename

# Organize into Artist/Album folders
music-recognize /path/to/music --organize --output /sorted

# Preview changes without modifying files
music-recognize /path/to/music --rename --dry-run
```

## 📖 Usage Examples

### Command Line

```bash
# Process single file
music-recognize song.mp3

# Process directory with custom template
music-recognize /music --rename --template "{artist}/{album}/{title}.mp3"

# Export results to JSON
music-recognize /music --output report.json

# Force re-recognition of already tagged files
music-recognize /music --force --overwrite

# Quiet mode (minimal output)
music-recognize /music -q

# Verbose mode (detailed logging)
music-recognize /music -v
```

### Python API

```python
import asyncio
from music_recognition import MusicRecognizer, recognize_and_tag

# Simple one-liner
asyncio.run(recognize_and_tag("/music", rename=True))

# Full control
async def process_collection():
    recognizer = MusicRecognizer(
        max_concurrent=5,
        delay_between_requests=0.5,
    )
    
    stats = await recognizer.process_directory(
        source_dir="/music",
        output_dir="/sorted",
        write_tags=True,
        rename=True,
        rename_template="{artist} - {title}.mp3",
        organize=True,
        skip_recognized=True,
        dry_run=False,
    )
    
    print(f"Recognized: {stats.recognized}/{stats.processed}")
    print(f"Success rate: {stats.success_rate:.1f}%")

asyncio.run(process_collection())
```

## ⚙️ CLI Options

```
usage: music-recognize [-h] [-o PATH] [--rename] [--template TPL] [--organize]
                       [--overwrite] [-f] [-c N] [--delay SEC] [-n] [-v] [-q]
                       path

Arguments:
  path                    File or directory to process

Options:
  -o, --output PATH       Output directory or report file (.json/.csv)
  --rename                Rename files based on metadata
  --template TPL          Filename template (default: "{artist} - {title}.mp3")
  --organize              Organize files into Artist/Album folders
  --overwrite             Overwrite existing ID3 tags
  -f, --force             Process files even if they have valid tags
  -c, --concurrent N      Max concurrent requests (default: 5)
  --delay SEC             Delay between requests (default: 0.5)
  -n, --dry-run           Preview changes without modifying files
  -v, --verbose           Verbose output
  -q, --quiet             Minimal output
```

### Template Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{artist}` | Artist name | Queen |
| `{title}` | Track title | Bohemian Rhapsody |
| `{album}` | Album name | A Night at the Opera |
| `{year}` | Release year | 1975 |
| `{genre}` | Genre | Rock |
| `{track}` | Track number | 01 |

## 📊 Output Example

```
╔══════════════════════════════════════════════════════════════╗
║  🎵 Music Recognition v1.0.0                                 ║
║  Identify • Tag • Rename • Organize                          ║
╚══════════════════════════════════════════════════════════════╝

Processing: /music/old_collection
Actions: tag, rename

[150/150] 100.0% ✓ Unknown Track.mp3

══════════════════════════════════════════════════
  SUMMARY
══════════════════════════════════════════════════
  Total files:    150
  Processed:      150
  Recognized:     142
  Failed:         5
  Skipped:        3
  Success rate:   94.7%
  Duration:       125.3s
══════════════════════════════════════════════════
```

## 🎯 Use Cases

- **Digital hoarders**: 50GB folder of `Track01.mp3` from 2005
- **DJs**: Tracks from old mixtapes without metadata
- **Media server admins**: Plex/Jellyfin shows "Unknown Artist"
- **Music collectors**: Vinyl rips without proper tags

## 🔧 Supported Formats

| Format | Read | Convert to MP3 |
|--------|------|----------------|
| MP3 | ✅ | — |
| WAV | ✅ | ✅ |
| FLAC | ✅ | ✅ |
| M4A | ✅ | ✅ |
| OGG | ✅ | ✅ |
| OPUS | ✅ | ✅ |

## 🧪 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run tests with coverage
pytest --cov=music_recognition --cov-report=html

# Format code
black src/
isort src/
```

## 📄 License

MIT License — use freely.

## 🙏 Credits

- [ShazamIO](https://github.com/dotX12/ShazamIO) — Python Shazam API wrapper
- [Mutagen](https://github.com/quodlibet/mutagen) — Audio metadata library
- [PyDub](https://github.com/jiaaro/pydub) — Audio format conversion

---

**Like this project?** Give it a ⭐ on [GitHub](https://github.com/formeo/music_recognition)!
