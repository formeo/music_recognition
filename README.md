
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-31013/)
[![Pylint](https://github.com/formeo/music_recognition/actions/workflows/pylint.yml/badge.svg)](https://github.com/formeo/music_recognition/actions/workflows/pylint.yml)
# Скрипты распознавания музыки

Позволяют понять что у вас за старые  mp3 на компе валяются


## класс Music 

### метод recognize_and_move 

входные параметры: искомая директория, и директория куда положить записи

Раскладывает песни из искомой директории в директорию назначения по артист/альбом/песня

натравливаете на директорию где все свалено в кучу и получаете упорядоченные каталоги с песнями, НЮАНС - работает только с mp3


### метод convert_files_to_mp3 

входной параметр - исходная директория с песнями

конвертирует все песни в mp3, НЮАНС - есть параметр удаления исходного файла, НЮАНС 2 - необходим  ffmpeg в PATH



## async music_shazam 

Распознает выши песни с помощью shazam

Входной параметр - исходная директория 
