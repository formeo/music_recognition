import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from mutagen import File
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class MusicService:
    MUSIC_FILES_EXTENSION = {'.mp3', '.MP3'}

    @staticmethod
    def __get_metadata(audio, key, default="Unknown"):
        """Helper method to extract metadata from audio tags."""
        try:
            if key in audio:
                return audio[key][0].encode('latin1').decode('cp1251')
        except Exception as e:
            logger.error(f'Error extracting {key}: {e}')
        return default

    @staticmethod
    def uniquify(path):
        """Generate a unique file name if the file already exists."""
        filename, extension = os.path.splitext(path)
        counter = 1

        while os.path.exists(path):
            path = f"{filename} ({counter}){extension}"
            counter += 1

        return path

    @staticmethod
    def __convert_file_to_mp3(absolute_file_path, remove_source=False):
        """Convert a file to MP3 format."""
        logger.info(f'Start converting file {absolute_file_path} to MP3')
        try:
            song = AudioSegment.from_file(absolute_file_path)
            new_file_name = f'{os.path.splitext(absolute_file_path)[0]}.mp3'
            song.export(new_file_name, format="mp3")
            logger.info(f'Converted file: {new_file_name}')

            if remove_source and os.path.exists(new_file_name):
                logger.info(f'Removing source file: {absolute_file_path}')
                os.remove(absolute_file_path)
        except Exception as e:
            logger.error(f'Failed to convert file {absolute_file_path}: {e}')
        logger.info(f'Conversion of file {absolute_file_path} finished')

    def convert_files_to_mp3(self, source_directory_path):
        """Convert all non-MP3 files in the directory to MP3 format."""
        with ThreadPoolExecutor() as executor:
            for root, _, files in os.walk(source_directory_path):
                for file in files:
                    absolute_path = os.path.join(root, file)
                    _, ext = os.path.splitext(file)
                    if ext not in self.MUSIC_FILES_EXTENSION:
                        executor.submit(self.__convert_file_to_mp3, absolute_path, remove_source=True)

    def recognize_and_move(self, source_directory_path, output_directory_path):
        """Recognize music files and move them to the output directory organized by artist and album."""
        with ThreadPoolExecutor() as executor:
            for root, _, files in os.walk(source_directory_path):
                for file in files:
                    absolute_path = os.path.join(root, file)
                    _, ext = os.path.splitext(file)
                    if ext in self.MUSIC_FILES_EXTENSION:
                        executor.submit(self._process_audio_file, absolute_path, output_directory_path)

    def _process_audio_file(self, file_path, output_directory_path):
        """Process a single audio file: extract metadata, create directories, and move the file."""
        try:
            # Read or add ID3 tags
            try:
                audio = EasyID3(file_path)
            except ID3NoHeaderError:
                audio = File(file_path, easy=True)
                audio.add_tags()

            # Extract metadata
            artist = self.__get_metadata(audio, 'artist', "Unknown Artist")
            album = self.__get_metadata(audio, 'album', "Unknown Album")
            title = self.__get_metadata(audio, 'title', os.path.basename(file_path))

            logger.info(f'Processing audio file: {file_path}, Artist: {artist}, Album: {album}, Title: {title}')

            # Define target directory
            target_directory = os.path.join(output_directory_path, artist, album)
            os.makedirs(target_directory, exist_ok=True)
            logger.info(f'Created directory: {target_directory}')

            # Generate unique file name
            new_audio_file_name = self.uniquify(os.path.join(target_directory, f"{title}.mp3"))
            logger.info(f'New audio file name: {new_audio_file_name}')

            # Move the file
            try:
                shutil.move(file_path, new_audio_file_name)
                logger.info(f'Moved file: {file_path} -> {new_audio_file_name}')
            except Exception as e:
                logger.error(f'Failed to move file {file_path} to {new_audio_file_name}: {e}')
        except Exception as e:
            logger.error(f'Error processing file {file_path}: {e}')