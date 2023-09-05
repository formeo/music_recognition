import os


class MusicService:

    def __init__(self, path):
        self.path = path

    def convert(self, cur):
        for dr in os.listdir(cur):
            abs_path = os.path.join(cur, dr)
            if os.path.isdir(abs_path):
                self.convert(abs_path)
            elif 'wma' in dr[-3:]:
                from pydub import AudioSegment
                print(abs_path)
                abs_path_prev = abs_path
                try:
                    wma_version = AudioSegment.from_file(abs_path)

                    pre, ext = os.path.splitext(abs_path)
                    abs_path = pre + ".mp3"
                    wma_version.export(abs_path, format="mp3")
                    print(f'prev path will be removed {abs_path_prev}')
                    os.remove(abs_path_prev)
                except:
                    continue

        def shazam(self, cur):
            for dr in os.listdir(cur):
                abs_path = os.path.join(cur, dr)
                if os.path.isdir(abs_path):
                    self.convert(abs_path)
                elif 'mp3' in dr[-3:] or 'MP3' in dr[-3:] :
                    from pydub import AudioSegment
                    print(abs_path)
                    abs_path_prev = abs_path
                    out = await shazam.recognize_song(abs_path)
                      track = out.get('track')
                      pprint(track.get('subtitle'))
                      pprint(track.get('title'))
                      try:
                          meta = EasyID3(abs_path)
                      except mutagen.id3.ID3NoHeaderError:
                         meta = mutagen.File(abs_path, easy=True)
                         meta.add_tags()

                      meta['title'] = track.get('title')
                      meta['artist'] = track.get('subtitle')

                      meta.save(abs_path, v1=2)

