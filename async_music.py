import asyncio
import logging
import os
from typing import Dict, Any, List

import mutagen
from mutagen.easyid3 import EasyID3
from shazamio import Shazam

logger = logging.getLogger(__name__)

MUSIC_FILES_EXTENSION = {'.mp3', '.MP3'}  # Используем множество для быстрого поиска


async def shazam_song(absolute_path: str) -> Dict[str, Any]:
    """Recognize song using Shazam API."""
    shazam = Shazam()
    try:
        logger.info(f"Recognizing song: {absolute_path}")
        return await shazam.recognize_song(absolute_path)
    except Exception as e:
        logger.error(f"Unable to recognize song {absolute_path}: {e}")
        return {}


async def process_file(absolute_path: str, shazam_all: bool):
    """Process a single music file: recognize and update metadata."""
    need_shazam = False

    try:
        meta = EasyID3(absolute_path)
    except mutagen.id3.ID3NoHeaderError:
        need_shazam = True
        meta = mutagen.File(absolute_path, easy=True)
        meta.add_tags()

    if need_shazam or shazam_all:
        shazamed = await shazam_song(absolute_path)
        if shazamed:
            try:
                track = shazamed.get('track', {})
                meta['title'] = track.get('title', ['Unknown title'])
                meta['artist'] = track.get('subtitle', ['Unknown artist'])

                # Extract album from sections (if available)
                sections = track.get('sections', [])
                album = (
                    sections[0].get('metadata', [{}])[0].get('text', 'Unknown album')
                    if sections and sections[0].get('metadata')
                    else 'Unknown album'
                )
                meta['album'] = [album]
            except Exception as e:
                logger.error(f"Error extracting metadata for {absolute_path}: {e}")
                meta['title'] = ['Unknown title']
                meta['artist'] = ['Unknown artist']
                meta['album'] = ['Unknown album']
        else:
            meta['title'] = ['Unknown title']
            meta['artist'] = ['Unknown artist']
            meta['album'] = ['Unknown album']

        # Save updated metadata
        meta.save(absolute_path, v1=2)
        logger.info(f"Updated metadata for file: {absolute_path}")


async def music_shazam(source_directory_path: str, shazam_all: bool = False):
    """Recognize music files in the directory and update metadata."""
    tasks: List[asyncio.Task] = []

    for root, _, files in os.walk(source_directory_path):
        for file in files:
            absolute_path = os.path.join(root, file)
            _, ext = os.path.splitext(file)

            if ext in MUSIC_FILES_EXTENSION:
                # Process each file asynchronously
                tasks.append(asyncio.create_task(process_file(absolute_path, shazam_all)))

    # Wait for all tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    source_directory = "/path"
    asyncio.run(music_shazam(source_directory, shazam_all=False))