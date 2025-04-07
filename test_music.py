import os
import shutil
import unittest
from unittest.mock import MagicMock, patch

from music import MusicService


class TestMusicService(unittest.TestCase):
    def setUp(self):
        # Создаем экземпляр MusicService
        self.service = MusicService()

        # Патчим зависимости
        self.file_path = "/mock/path/to/audio.mp3"
        self.output_directory_path = "/mock/output/directory"

        # Мокаем EasyID3 и File
        self.mock_easyid3 = MagicMock()
        self.mock_file = MagicMock()

        # Мокаем os.makedirs и shutil.move
        self.mock_makedirs = MagicMock()
        self.mock_move = MagicMock()
    #
    # @patch("music.EasyID3")
    # @patch("music.File")
    # @patch("music.os.makedirs")
    # @patch("music.shutil.move")
    # def test_process_audio_file(
    #     self,
    #     mock_move,
    #     mock_makedirs,
    #     mock_file,
    #     mock_easyid3,
    # ):
    #     """
    #     Тестирует функцию _process_audio_file.
    #     """
    #     # Настройка моков
    #     mock_easyid3.side_effect = Exception("No ID3 header")  # Симулируем отсутствие ID3 тегов
    #     mock_file.return_value.add_tags.return_value = None
    #     mock_file.return_value.get.side_effect = lambda key, default: {
    #         "artist": "Test Artist",
    #         "album": "Test Album",
    #         "title": "Test Title",
    #     }.get(key, default)
    #
    #     # Вызываем тестируемую функцию
    #     self.service._process_audio_file(self.file_path, self.output_directory_path)
    #
    #     # Проверяем вызовы
    #     mock_file.assert_called_once_with(self.file_path, easy=True)
    #     mock_file.return_value.add_tags.assert_called_once()
    #     mock_makedirs.assert_called_once_with(
    #         os.path.join(self.output_directory_path, "Test Artist", "Test Album"),
    #         exist_ok=True,
    #     )
    #     mock_move.assert_called_once_with(
    #         self.file_path,
    #         unittest.mock.ANY,  # Путь к новому файлу может быть сложным для проверки напрямую
    #     )

    @patch("music.EasyID3")
    @patch("music.File")
    @patch("music.os.makedirs")
    @patch("music.shutil.move")
    def test_process_audio_file_with_errors(
        self,
        mock_move,
        mock_makedirs,
        mock_file,
        mock_easyid3,
    ):
        """
        Тестирует обработку ошибок в функции _process_audio_file.
        """
        # Симулируем ошибку при чтении метаданных
        mock_easyid3.side_effect = Exception("No ID3 header")
        mock_file.side_effect = Exception("File error")

        # Вызываем тестируемую функцию
        with self.assertLogs(level="ERROR") as log:
            self.service._process_audio_file(self.file_path, self.output_directory_path)

        # Проверяем логирование ошибок
        self.assertIn("Error processing file", log.output[0])

        # Убеждаемся, что os.makedirs и shutil.move не вызывались
        mock_makedirs.assert_not_called()
        mock_move.assert_not_called()

if __name__ == "__main__":
    unittest.main()