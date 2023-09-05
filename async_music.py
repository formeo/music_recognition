import asyncio
import logging
import os
from typing import Dict, Any

import mutagen
from mutagen.easyid3 import EasyID3
from shazamio import Shazam

logger = logging.getLogger(__name__)

MUSIC_FILES_EXTENSION = ['mp3', 'MP3', ]


async def shazam_song(absolute_path) -> Dict[str, Any]:
    shazam = Shazam()
    try:
        return await shazam.recognize_song(absolute_path)
    except Exception as e:
        logger.error(f'unable to recognize song {e}')
        return {}


async def music_shazam(source_directory_path, shazam_all: bool = False):
    for dr in os.listdir(source_directory_path):

        absolute_path = os.path.join(source_directory_path, dr)
        if os.path.isdir(absolute_path):
            await music_shazam(absolute_path)
        else:
            need_shazam = False
            _, file_extension = os.path.splitext(absolute_path)
            if file_extension in MUSIC_FILES_EXTENSION:
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
                            # TODO в некоторых песнях есть жанр и текст - надо потом добавить
                            track = shazamed.get('track')
                            meta['title'] = track.get('title')
                            meta['artist'] = track.get('subtitle')
                            meta['album'] = track.get('sections')[0].get('metadata')[0].get('text')
                        except:
                            meta['title'] = 'Unknown title'
                            meta['artist'] = 'Unknown artist'
                            meta['album'] = 'Unknown album'
                    else:
                        meta['title'] = 'Unknown title'
                        meta['artist'] = 'Unknown artist'
                        meta['album'] = 'Unknown album'
                    meta.save(absolute_path, v1=2)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(music_shazam("/path"))
