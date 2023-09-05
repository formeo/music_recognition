# import shutil
# from pprint import pprint
# from random import randrange
#
# import requests
#
# from reddit import Reddit
# from ya_disk import YandexDisk
#
# TOKEN = "y0_AgAAAAAAQlimAADLWwAAAADaiAtfH6uWj-FAQ_yG4Qpc-miReb6IAnI"
#
# # def test_request():
# #     url = "https://httpbin.org/get"
# #     params = {"model": "nike123"}
# #     headers = {"Authorization": "secret - token - 123"}
# #     response = requests.get(url=url, params=params, headers=headers)
# #     pprint(response.json())
# #     if response.status_code != 200:
# #         print(f'status_code: {response.status_code}')
#
# from requests.auth import HTTPBasicAuth
#
# # Making a get request
# # response = requests.get('https://api.github.com / user, ',
# #                         auth=HTTPBasicAuth('user', 'pass'))
#
# import os
# from mutagen.easyid3 import EasyID3
#
# cp1252 = {
#     # from http://www.microsoft.com/typography/unicode/1252.htm
#     u"\u20AC": u"\x80",  # EURO SIGN
#     u"\u201A": u"\x82",  # SINGLE LOW-9 QUOTATION MARK
#     u"\u0192": u"\x83",  # LATIN SMALL LETTER F WITH HOOK
#     u"\u201E": u"\x84",  # DOUBLE LOW-9 QUOTATION MARK
#     u"\u2026": u"\x85",  # HORIZONTAL ELLIPSIS
#     u"\u2020": u"\x86",  # DAGGER
#     u"\u2021": u"\x87",  # DOUBLE DAGGER
#     u"\u02C6": u"\x88",  # MODIFIER LETTER CIRCUMFLEX ACCENT
#     u"\u2030": u"\x89",  # PER MILLE SIGN
#     u"\u0160": u"\x8A",  # LATIN CAPITAL LETTER S WITH CARON
#     u"\u2039": u"\x8B",  # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
#     u"\u0152": u"\x8C",  # LATIN CAPITAL LIGATURE OE
#     u"\u017D": u"\x8E",  # LATIN CAPITAL LETTER Z WITH CARON
#     u"\u2018": u"\x91",  # LEFT SINGLE QUOTATION MARK
#     u"\u2019": u"\x92",  # RIGHT SINGLE QUOTATION MARK
#     u"\u201C": u"\x93",  # LEFT DOUBLE QUOTATION MARK
#     u"\u201D": u"\x94",  # RIGHT DOUBLE QUOTATION MARK
#     u"\u2022": u"\x95",  # BULLET
#     u"\u2013": u"\x96",  # EN DASH
#     u"\u2014": u"\x97",  # EM DASH
#     u"\u02DC": u"\x98",  # SMALL TILDE
#     u"\u2122": u"\x99",  # TRADE MARK SIGN
#     u"\u0161": u"\x9A",  # LATIN SMALL LETTER S WITH CARON
#     u"\u203A": u"\x9B",  # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
#     u"\u0153": u"\x9C",  # LATIN SMALL LIGATURE OE
#     u"\u017E": u"\x9E",  # LATIN SMALL LETTER Z WITH CARON
#     u"\u0178": u"\x9F",  # LATIN CAPITAL LETTER Y WITH DIAERESIS
# }
#
#
#
#
#
import shutil
from random import randrange
import aiohttp
import mutagen
from mutagen.easyid3 import EasyID3
from shazamio import Shazam
import concurrent.futures
import asyncio
import os



def go(cur):
    # print('go ' + cur)

    for dr in os.listdir(cur):

        abs_path = os.path.join(cur, dr)


        if os.path.isdir(abs_path):
            go(abs_path)
        elif 'mp3' in dr[-3:]:
            #
            # from pydub import AudioSegment
            # print(abs_path)
            # abs_path_prev = abs_path
            # wma_version = AudioSegment.from_file(abs_path)
            #
            # pre, ext = os.path.splitext(abs_path)
            # abs_path = pre + "_.mp3"
            # wma_version.export(abs_path, format="mp3")
            # os.remove(abs_path_prev)

            try:
                audio = EasyID3(abs_path)
                print(audio)
            except Exception as e:
                print(e)
                continue
            if 'artist' in audio:
                try:
                    artist = audio['artist'][0].encode('latin1').decode('cp1251')
                except:
                    artist = "Unknown artist"
            else:
                artist = "Unknown artist"
            if 'album' in audio:
                try:
                    album = audio['album'][0].encode('latin1').decode('cp1251')
                except:
                    album = "Unknown album"
            else:
                album = "Unknown album"

            directory = os.path.join("F:\music", artist, album)
            try:

                print(directory)
                isExist = os.path.exists(directory)
                if not isExist:
                    # Create a new directory because it does not exist
                    os.makedirs(directory)
                    print("The new directory is created!")
            except Exception as e:
                print("directory")
                print(e)
                continue

            if 'title' in audio:
                try:
                    title = audio['title'][0].encode('latin1').decode('cp1251')
                except:
                    title = "Unknown title"
            else:
                title = "Unknown title"

            # Initial new name
            new_name = os.path.join(directory, title)
            print("new_name")

            print(new_name + '.mp3')
            new_name_full = new_name + '.mp3'
            if os.path.isfile(new_name_full):
                new_name_full = new_name + str(randrange(2000)) + '.mp3'
            try:
                shutil.move(abs_path, new_name_full)
            except Exception as e:
                print("cut")
                print(e)
                continue

#
# from music import MusicService
#

def rename(path):
    for dr in os.listdir(path):
        abs_path = os.path.join(path, dr)
        print(abs_path)
        try:
            audio = EasyID3(abs_path)
            print(audio)
            break
            album = audio['album'][0]
            directory = os.path.join(r"F:\music\MakSim", album)
            title = audio['title'][0]
            isExist = os.path.exists(directory)
            if not isExist:
                # Create a new directory because it does not exist
                os.makedirs(directory)
                print("The new directory is created!")
            new_name = os.path.join(directory, title)
            print("new_name")
            print(new_name + '.mp3')
            new_name_full = new_name + '.mp3'
            try:
                shutil.copy(abs_path, new_name_full)
            except Exception as e:
                print("cut")
                print(e)
                continue
        except:
            continue


# if __name__ == '__main__':
#
#     rename(r'F:\music\Слёзы Асфальта\Unknown album')

import asyncio
from pprint import pprint


# def list_files():
#     return os.listdir(r"F:\rom\Music\Music\Зарубежка\ERA")

# async def on_got_files(fut):
#    print("got files {}".format(fut.result()))
#    shazam = Shazam()
#    out = await shazam.recognize_song(r"F:\rom\Music\музыка с папки\02cbf3fe6e30.mp3")
#    #   pprint(out)
#
#    loop.stop()
#
#
# async def main():
#     async with aiohttp.ClientSession() as session:
#         tasks = {get_lenght(session, url) for url in lst}
#         for task in asyncio.as_completed(tasks):
#             result = await task
#             print(result)
#
# def main():
#    with concurrent.futures.ProcessPoolExecutor() as executor:
#        fut = loop.run_in_executor(executor, list_files)
#        fut.add_done_callback(on_got_files)
#        print("Listing files asynchronously")
#
# if __name__ == "__main__":
#    loop = asyncio.get_event_loop()
#    loop.call_soon(main)
#    loop.run_forever()

async def go(cur):
    shazam = Shazam()
    for dr in os.listdir(cur):

        abs_path = os.path.join(cur, dr)

        if os.path.isdir(abs_path):
            await go(abs_path)
        elif 'mp3' in dr[-3:] or 'MP3' in dr[-3:]:
            pprint(abs_path)
            try:
                out = await shazam.recognize_song(abs_path)
            except:
                continue
            if out:
              track = out.get('track')


            else:
                continue
            pprint(track)
            if track:


                pprint(track.get('subtitle'))
                pprint(track.get('title'))
            else:
                continue
            try:
                meta = EasyID3(abs_path)
            except mutagen.id3.ID3NoHeaderError:
                meta = mutagen.File(abs_path, easy=True)
                meta.add_tags()
            try:
                meta['title'] = track.get('title')
                meta['artist'] = track.get('subtitle')
                try:
                    meta['album'] = track.get('sections')[0].get('metadata')[0].get('text')
                except:
                    meta['album'] = 'Неизвестный альбом'


                meta.save(abs_path, v1=2)
            except:
                continue


loop = asyncio.get_event_loop()
loop.run_until_complete(go(r"F:\music\Unknown artist"))
