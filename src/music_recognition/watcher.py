import asyncio
from pathlib import Path
from typing import Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from music_recognition import MusicRecognizer
from music_recognition.core import logger


class MusicFolderWatcher:
    """Watch directory for new music files and auto-process them."""

    def __init__(
            self,
            recognizer: MusicRecognizer,
            watch_dir: str,
            output_dir: Optional[str] = None,
            rename: bool = True,
            organize: bool = False,
    ):
        self.recognizer = recognizer
        self.watch_dir = Path(watch_dir)
        self.output_dir = output_dir
        self.rename = rename
        self.organize = organize
        self._queue: asyncio.Queue = asyncio.Queue()
        self._observer = None

    async def start(self):
        """Start watching directory."""
        handler = _FileHandler(self._queue, self.recognizer.SUPPORTED_EXTENSIONS)

        self._observer = Observer()
        self._observer.schedule(handler, str(self.watch_dir), recursive=True)
        self._observer.start()

        logger.info(f"Watching: {self.watch_dir}")

        # Process queue
        while True:
            file_path = await self._queue.get()

            # Wait for file to be fully written
            await asyncio.sleep(1.0)

            try:
                result = await self.recognizer.process_file(
                    file_path=file_path,
                    output_dir=self.output_dir,
                    rename=self.rename,
                    organize=self.organize,
                )

                if result.status == "success":
                    logger.info(f"✓ {result.track_info.artist} - {result.track_info.title}")
                else:
                    logger.warning(f"✗ {file_path}: {result.error}")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

    def stop(self):
        """Stop watching."""
        if self._observer:
            self._observer.stop()
            self._observer.join()


class _FileHandler(FileSystemEventHandler):
    def __init__(self, queue: asyncio.Queue, extensions: set):
        self.queue = queue
        self.extensions = extensions

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            return
        if Path(event.src_path).suffix.lower() in self.extensions:
            asyncio.run_coroutine_threadsafe(
                self.queue.put(event.src_path),
                asyncio.get_event_loop()
            )
