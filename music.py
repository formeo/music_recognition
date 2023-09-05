import logging
import os
import shutil

import mutagen
from mutagen.easyid3 import EasyID3
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class MusicService:
    MUSIC_FILES_EXTENSION = ['mp3', 'MP3', ]

    @staticmethod
    def __get_artist(audio: EasyID3) -> str:
        artist = "Unknown artist"

        if 'artist' in audio:
            try:
                artist = audio['artist'][0].encode('latin1').decode('cp1251')
            except Exception as e:
                logger.error(f'artist not found: {e}')

        return artist

    @staticmethod
    def __get_album(audio: EasyID3) -> str:
        album = "Unknown album"

        if 'album' in audio:
            try:
                album = audio['album'][0].encode('latin1').decode('cp1251')
            except Exception as e:
                logger.error(f'album not found: {e}')

        return album

    @staticmethod
    def __get_title(audio: EasyID3) -> str:
        title = "Unknown title"

        if 'title' in audio:
            try:
                title = audio['title'][0].encode('latin1').decode('cp1251')
            except Exception as e:
                logger.error(f'title not found: {e}')

        return title

    @staticmethod
    def uniquify(path):
        filename, extension = os.path.splitext(path)
        counter = 1

        while os.path.exists(path):
            path = filename + " (" + str(counter) + ")" + extension
            counter += 1

        return path

    @staticmethod
    def __convert_file_to_mp3(absolute_file_path: str, remove_source: bool = False):
        logger.info(f'start convert file {absolute_file_path} to mp3')
        song = AudioSegment.from_file(absolute_file_path)
        file_name, file_extension = os.path.splitext(absolute_file_path)
        new_file_name = f'{file_name}.mp3'
        logger.info(f'new file is {new_file_name}')
        song.export(new_file_name, format="mp3")

        if os.path.exists(new_file_name) and remove_source:
            logger.info(f'file {absolute_file_path} will be remove')
            os.remove(absolute_file_path)

        logger.info(f'convert file {absolute_file_path} to mp3 finished')

    def convert_files_to_mp3(self, source_directory_path):
        for path in os.listdir(source_directory_path):
            absolute_path = os.path.join(source_directory_path, path)
            if not os.path.isdir(absolute_path):
                _, file_extension = os.path.splitext(absolute_path)
                if file_extension in self.MUSIC_FILES_EXTENSION:
                    continue
                self.__convert_file_to_mp3(absolute_path, remove_source=True)
            else:
                self.convert_files_to_mp3(absolute_path)

    def recognize_and_move(self, source_directory_path, output_directory_path):
        for path in os.listdir(source_directory_path):
            absolute_path = os.path.join(source_directory_path, path)
            if not os.path.isdir(absolute_path):

                _, file_extension = os.path.splitext(absolute_path)
                if file_extension in self.MUSIC_FILES_EXTENSION:

                    try:
                        audio = EasyID3(absolute_path)
                    except mutagen.id3.ID3NoHeaderError:
                        audio = mutagen.File(absolute_path, easy=True)
                        audio.add_tags()

                    artist = self.__get_artist(audio)
                    album = self.__get_album(audio)
                    title = self.__get_title(audio)
                    logger.info(f'audio file {absolute_path}, artist {artist}, album {album} title {title}')

                    directory = os.path.join(output_directory_path, artist, album)

                    logger.info(f' output directory {directory}')

                    is_exist = os.path.exists(directory)
                    if not is_exist:
                        # Create a new directory because it does not exist
                        os.makedirs(directory)
                        logger.info("The new directory is created!")

                    new_audio_file_name = self.uniquify(os.path.join(directory, title) + '.mp3')
                    logger.info(f'new audio file name is {new_audio_file_name}')

                    try:
                        shutil.move(absolute_path, new_audio_file_name)
                    except Exception as e:
                        logger.error(f'cannot move file {absolute_path} to new file destination {new_audio_file_name} '
                                     f'due to {e}')
                        continue
            else:
                self.recognize_and_move(absolute_path, output_directory_path)
