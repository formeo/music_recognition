# 🎵 Music Recognition

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Actions](https://github.com/formeo/music_recognition/actions/workflows/python-package.yml/badge.svg)](https://github.com/formeo/music_recognition/actions)

**Bulk music identification and tagging tool** — bring order to your chaotic music collection.

## The Problem

We all have them: old MP3 collections full of `Track01.mp3`, `Unknown - Unknown.mp3`, or just random numbers. Manually identifying each track is tedious and time-consuming.

## The Solution

Music Recognition automatically:
- 🔍 Identifies tracks via Shazam API
- 📝 Extracts metadata: artist, title, album, year
- 🔄 Converts audio formats when needed
- ⚡ Processes files asynchronously for maximum speed

## Quick Start

```bash
# Clone the repo
git clone https://github.com/formeo/music_recognition.git
cd music_recognition

# Set up environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run
python recognize.py /path/to/music/folder
```

## Usage

### CLI — Recognize a folder

```bash
python recognize.py /path/to/audio/files
```

### Programmatic API

```python
from music import MusicService

service = MusicService()

# Convert files to mp3 if needed
service.convert_files_to_mp3("/path/to/music")

# Recognize a single file
result = service.recognize_file("track.mp3")
print(f"{result['artist']} - {result['track']}")
```

### Async Processing (for large collections)

```python
from async_music import AsyncMusicService
import asyncio

async def main():
    service = AsyncMusicService()
    results = await service.process_directory("/path/to/music")
    for file, info in results.items():
        print(f"{file}: {info['artist']} - {info['track']}")

asyncio.run(main())
```

## Supported Formats

| Format | Read | Convert |
|--------|------|---------|
| MP3    | ✅    | —       |
| WAV    | ✅    | ✅ → MP3 |
| FLAC   | ✅    | ✅ → MP3 |
| OGG    | ✅    | ✅ → MP3 |
| M4A    | ✅    | ✅ → MP3 |

## Example Output

```json
{
  "track": "Bohemian Rhapsody",
  "artist": "Queen",
  "album": "A Night at the Opera",
  "year": "1975",
  "genre": "Rock",
  "cover_url": "https://..."
}
```

## Requirements

- Python 3.8+
- FFmpeg (for format conversion)

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Project Structure

```
music_recognition/
├── recognize.py      # CLI entry point
├── music.py          # Synchronous service
├── async_music.py    # Asynchronous service
├── test_music.py     # Tests
└── requirements.txt  # Dependencies
```

## Limitations

- Shazam API has rate limits
- Very rare or live recordings may not be recognized
- Requires internet connection

## Roadmap

- [ ] Auto-write ID3 tags to files
- [ ] Rename files using templates (`{artist} - {track}.mp3`)
- [ ] MusicBrainz integration for extended metadata
- [ ] Local fingerprinting via Chromaprint/AcoustID
- [ ] GUI interface
- [ ] Docker image
- [ ] Watch mode for new files

## Use Cases

- **Digital hoarders**: Finally organize that 50GB music folder from 2005
- **DJs**: Identify tracks from old mixtapes and recordings
- **Media server admins**: Prepare libraries for Plex, Jellyfin, Navidrome
- **Music collectors**: Tag and catalog vinyl rips and rare recordings

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## License

MIT License — use freely.

## Author

[@formeo](https://github.com/formeo) • Senior Python Developer

---

**Found a bug or have an idea?** [Open an issue](https://github.com/formeo/music_recognition/issues)

**Like this project?** Give it a ⭐ on GitHub!
