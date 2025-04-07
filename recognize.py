import argparse
import os

from music import MusicService


def process_directory(directory):
    """
    Обрабатывает указанную директорию: проверяет её существование,
    выводит список файлов и поддиректорий.
    """
    if not os.path.exists(directory):
        print(f"Ошибка: Директория '{directory}' не существует.")
        return

    if not os.path.isdir(directory):
        print(f"Ошибка: '{directory}' не является директорией.")
        return


def main():
    # Создаем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="Обработка директории.")

    # Добавляем аргумент для директории
    parser.add_argument(
        "directory",
        type=str,
        help="Путь к директориис музыкальными файлами, которую нужно обработать."
    )

    # Парсим аргументы
    args = parser.parse_args()

    music_service = MusicService()
    music_service.convert_files_to_mp3(args.directory)


if __name__ == "__main__":
    main()
