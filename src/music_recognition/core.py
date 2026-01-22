"""
Music Recognition Service
Identify unknown MP3 files using Shazam API, write ID3 tags, rename and organize.

Usage:
    from music_recognition import MusicRecognizer
    
    recognizer = MusicRecognizer()
    await recognizer.process_directory("/music", rename=True, organize=True)
"""

import asyncio
import logging
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from pydub import AudioSegment
from shazamio import Shazam

__version__ = "1.1.0"
__author__ = "formeo"

from music_recognition.cache import RecognitionCache
from models.models import TrackInfo

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a single file."""
    original_path: str
    final_path: str = ""
    status: str = "pending"  # pending, success, failed, skipped
    track_info: Optional[TrackInfo] = None
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_path": self.original_path,
            "final_path": self.final_path,
            "status": self.status,
            "error": self.error,
            "track": self.track_info.to_dict() if self.track_info else None,
        }


@dataclass
class ProcessingStats:
    """Statistics for batch processing."""
    total: int = 0
    processed: int = 0
    recognized: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    results: List[ProcessingResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate recognition success rate."""
        if self.processed == 0:
            return 0.0
        return (self.recognized / self.processed) * 100

    @property
    def duration_seconds(self) -> float:
        """Get processing duration in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "total": self.total,
            "processed": self.processed,
            "recognized": self.recognized,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": round(self.success_rate, 1),
            "duration_seconds": round(self.duration_seconds, 1),
            "files": [r.to_dict() for r in self.results],
        }


# ============================================================
# Main Service
# ============================================================

class MusicRecognizer:
    """
    Music recognition service with Shazam integration.
    
    Features:
    - Async batch processing with rate limiting
    - ID3 tag writing
    - File renaming with customizable templates
    - Directory organization (Artist/Album structure)
    - Multiple audio format support with conversion
    """

    SUPPORTED_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.opus', '.wma', '.aac'}
    MP3_EXTENSION = '.mp3'

    # Characters not allowed in filenames
    FORBIDDEN_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

    def __init__(
            self,
            max_concurrent: int = 5,
            delay_between_requests: float = 0.5,
            retry_attempts: int = 2,
            use_cache: bool = True,
            cache_path: Optional[str] = None,
    ):
        """
        Initialize the recognizer.
        
        Args:
            max_concurrent: Maximum concurrent Shazam requests
            delay_between_requests: Delay between requests in seconds
            retry_attempts: Number of retry attempts on failure
        """
        self.shazam = Shazam()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.delay = delay_between_requests
        self.retry_attempts = retry_attempts
        self.cache = RecognitionCache(cache_path) if use_cache else None

    # ==================== Recognition ====================

    async def recognize_file(self, file_path: str, skip_cache: bool = False) -> TrackInfo:
        """Recognize with cache support."""
        if self.cache and not skip_cache:
            cached = self.cache.get(file_path)
            if cached:
                logger.debug(f"Cache hit: {file_path}")
                return cached

        info = await self._recognize_shazam(file_path)

        if self.cache and info.is_recognized:
            self.cache.set(file_path, info)

        return info

    async def _recognize_shazam(self, file_path: str) -> TrackInfo:
        """
        Recognize a single audio file using Shazam.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            TrackInfo with recognized metadata
        """
        async with self.semaphore:
            for attempt in range(self.retry_attempts + 1):
                try:
                    logger.debug(f"Recognizing (attempt {attempt + 1}): {file_path}")

                    result = await self.shazam.recognize(file_path)

                    if self.delay > 0:
                        await asyncio.sleep(self.delay)

                    return self._parse_shazam_response(result)

                except Exception as e:
                    logger.warning(f"Recognition attempt {attempt + 1} failed for {file_path}: {e}")
                    if attempt < self.retry_attempts:
                        await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(f"All recognition attempts failed for {file_path}")
                        return TrackInfo()

        return TrackInfo()

    def _parse_shazam_response(self, response: Dict[str, Any]) -> TrackInfo:
        """Parse Shazam API response into TrackInfo."""
        if not response or 'track' not in response:
            return TrackInfo()

        track = response['track']
        info = TrackInfo(
            title=track.get('title', 'Unknown'),
            artist=track.get('subtitle', 'Unknown'),
            shazam_id=track.get('key', ''),
        )

        # Extract additional metadata from sections
        for section in track.get('sections', []):
            if section.get('type') == 'SONG':
                for meta in section.get('metadata', []):
                    meta_title = meta.get('title', '')
                    meta_text = meta.get('text', '')

                    if meta_title == 'Album':
                        info.album = meta_text
                    elif meta_title == 'Released':
                        # Extract year from date string
                        info.year = meta_text[:4] if meta_text else ''

        # Get genre from hub actions
        if 'hub' in track:
            for action in track['hub'].get('options', []):
                if 'listcaption' in action:
                    info.genre = action.get('listcaption', '')
                    break

        # Get cover art URL
        if 'images' in track:
            info.cover_url = track['images'].get('coverart', '')

        return info

    # ==================== Tag Operations ====================

    @staticmethod
    def read_existing_tags(file_path: str) -> TrackInfo:
        """Read existing ID3 tags from file."""
        try:
            audio = EasyID3(file_path)
            return TrackInfo(
                title=audio.get('title', ['Unknown'])[0],
                artist=audio.get('artist', ['Unknown'])[0],
                album=audio.get('album', ['Unknown Album'])[0],
                year=audio.get('date', [''])[0][:4] if audio.get('date') else '',
                genre=audio.get('genre', [''])[0] if audio.get('genre') else '',
                track_number=audio.get('tracknumber', [''])[0] if audio.get('tracknumber') else '',
            )
        except Exception:
            return TrackInfo()

    @staticmethod
    def has_valid_tags(file_path: str) -> bool:
        """Check if file has valid (non-empty) ID3 tags."""
        try:
            audio = EasyID3(file_path)
            title = audio.get('title', [''])[0]
            artist = audio.get('artist', [''])[0]
            return bool(title and artist and title != 'Unknown' and artist != 'Unknown')
        except Exception:
            return False

    @staticmethod
    def write_tags(file_path: str, info: TrackInfo, overwrite: bool = False) -> bool:
        """
        Write ID3 tags to an MP3 file.
        
        Args:
            file_path: Path to the MP3 file
            info: TrackInfo with metadata
            overwrite: If True, overwrite existing tags
            
        Returns:
            True if successful
        """
        if not info.is_recognized:
            logger.warning(f"Skipping unrecognized track: {file_path}")
            return False

        try:
            # Load or create tags
            try:
                audio = EasyID3(file_path)
            except ID3NoHeaderError:
                audio = mutagen.File(file_path, easy=True)
                audio.add_tags()

            # Check existing tags
            if not overwrite:
                existing_title = audio.get('title', [''])[0]
                existing_artist = audio.get('artist', [''])[0]
                if existing_title and existing_artist:
                    logger.debug(f"Tags exist, skipping: {file_path}")
                    return False

            # Write tags
            audio['title'] = info.title
            audio['artist'] = info.artist
            audio['album'] = info.album

            if info.year:
                audio['date'] = info.year
            if info.genre:
                audio['genre'] = info.genre
            if info.track_number:
                audio['tracknumber'] = info.track_number

            audio.save()
            logger.info(f"Tags written: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error writing tags to {file_path}: {e}")
            return False

    # ==================== File Operations ====================

    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize string for use as filename.
        
        Removes forbidden characters and limits length.
        """
        # Replace forbidden characters with underscore
        name = self.FORBIDDEN_CHARS.sub('_', name)
        # Remove leading/trailing spaces and dots
        name = name.strip(' .')
        # Limit length (255 is common filesystem limit)
        if len(name) > 200:
            name = name[:200]
        return name or "Unknown"

    def generate_filename(
            self,
            info: TrackInfo,
            template: str = "{artist} - {title}.mp3"
    ) -> str:
        """
        Generate filename from template.
        
        Available placeholders:
        - {artist}: Artist name
        - {title}: Track title
        - {album}: Album name
        - {year}: Release year
        - {genre}: Genre
        - {track}: Track number
        """
        try:
            filename = template.format(
                artist=self.sanitize_filename(info.artist),
                title=self.sanitize_filename(info.title),
                album=self.sanitize_filename(info.album),
                year=self.sanitize_filename(info.year) if info.year else "Unknown",
                genre=self.sanitize_filename(info.genre) if info.genre else "Unknown",
                track=info.track_number or "00",
            )
            return filename
        except KeyError as e:
            logger.warning(f"Unknown placeholder in template: {e}")
            return f"{self.sanitize_filename(info.artist)} - {self.sanitize_filename(info.title)}.mp3"

    @staticmethod
    def uniquify(path: str) -> str:
        """Generate unique filename if file already exists."""
        if not os.path.exists(path):
            return path

        base, ext = os.path.splitext(path)
        counter = 1

        while os.path.exists(path):
            path = f"{base} ({counter}){ext}"
            counter += 1

        return path

    def convert_to_mp3(
            self,
            file_path: str,
            remove_source: bool = False,
            bitrate: str = "320k"
    ) -> Optional[str]:
        """
        Convert audio file to MP3 format.
        
        Args:
            file_path: Path to source file
            remove_source: Delete source file after conversion
            bitrate: Output bitrate
            
        Returns:
            Path to converted file, or None if failed
        """
        if Path(file_path).suffix.lower() == self.MP3_EXTENSION:
            return file_path

        logger.info(f"Converting to MP3: {file_path}")

        try:
            audio = AudioSegment.from_file(file_path)
            new_path = f"{os.path.splitext(file_path)[0]}.mp3"
            new_path = self.uniquify(new_path)

            audio.export(new_path, format="mp3", bitrate=bitrate)
            logger.info(f"Converted: {new_path}")

            if remove_source and os.path.exists(new_path):
                os.remove(file_path)
                logger.debug(f"Removed source: {file_path}")

            return new_path

        except Exception as e:
            logger.error(f"Conversion failed for {file_path}: {e}")
            return None

    # ==================== Processing ====================

    async def process_file(
            self,
            file_path: str,
            output_dir: Optional[str] = None,
            write_tags: bool = True,
            rename: bool = False,
            rename_template: str = "{artist} - {title}.mp3",
            organize: bool = False,
            overwrite_tags: bool = False,
            skip_recognized: bool = True,
            dry_run: bool = False,
    ) -> ProcessingResult:
        """
        Process a single music file.
        
        Args:
            file_path: Path to the audio file
            output_dir: Output directory for organized files
            write_tags: Write ID3 tags after recognition
            rename: Rename file based on metadata
            rename_template: Template for new filename
            organize: Organize into Artist/Album folders
            overwrite_tags: Overwrite existing tags
            skip_recognized: Skip files that already have valid tags
            dry_run: Preview without making changes
            
        Returns:
            ProcessingResult with status and info
        """
        result = ProcessingResult(original_path=file_path)

        try:
            # Check if we should skip this file
            if skip_recognized and not overwrite_tags:
                if self.has_valid_tags(file_path):
                    existing = self.read_existing_tags(file_path)
                    result.status = "skipped"
                    result.track_info = existing
                    result.final_path = file_path
                    logger.debug(f"Skipping (has tags): {file_path}")
                    return result

            # Recognize
            info = await self.recognize_file(file_path)
            result.track_info = info

            if not info.is_recognized:
                result.status = "failed"
                result.error = "Could not recognize"
                result.final_path = file_path
                return result

            current_path = file_path

            # Write tags
            if write_tags and not dry_run:
                self.write_tags(current_path, info, overwrite=overwrite_tags)
            elif write_tags and dry_run:
                logger.info(f"[DRY RUN] Would write tags: {info.artist} - {info.title}")

            # Determine target directory
            if organize and output_dir:
                target_dir = Path(output_dir) / self.sanitize_filename(info.artist) / self.sanitize_filename(info.album)
            elif output_dir:
                target_dir = Path(output_dir)
            else:
                target_dir = Path(current_path).parent

            # Determine final filename
            if rename:
                new_filename = self.generate_filename(info, rename_template)
            else:
                new_filename = Path(current_path).name

            final_path = target_dir / new_filename
            final_path_str = self.uniquify(str(final_path))

            # Move/rename if needed
            if str(final_path_str) != current_path:
                if dry_run:
                    logger.info(f"[DRY RUN] Would move: {current_path} -> {final_path_str}")
                else:
                    # Create directory if needed
                    Path(final_path_str).parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(current_path, final_path_str)
                    logger.info(f"Moved: {current_path} -> {final_path_str}")
                current_path = final_path_str

            result.status = "success"
            result.final_path = current_path

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            result.status = "failed"
            result.error = str(e)
            result.final_path = file_path

        return result

    async def process_directory(
            self,
            source_dir: str,
            output_dir: Optional[str] = None,
            write_tags: bool = True,
            rename: bool = False,
            rename_template: str = "{artist} - {title}.mp3",
            organize: bool = False,
            overwrite_tags: bool = False,
            skip_recognized: bool = True,
            convert_formats: bool = True,
            dry_run: bool = False,
            progress_callback: Optional[callable] = None,
    ) -> ProcessingStats:
        """
        Process all music files in a directory.
        
        Args:
            source_dir: Source directory path
            output_dir: Output directory (for organizing)
            write_tags: Write ID3 tags after recognition
            rename: Rename files based on metadata
            rename_template: Template for new filenames
            organize: Organize into Artist/Album folders
            overwrite_tags: Overwrite existing tags
            skip_recognized: Skip files that already have valid tags
            convert_formats: Convert non-MP3 files to MP3
            dry_run: Preview without making changes
            progress_callback: Called with (current, total, result) for each file
            
        Returns:
            ProcessingStats with results and statistics
        """
        stats = ProcessingStats()
        source_path = Path(source_dir)

        # Collect files to process
        files_to_process = []
        for file_path in source_path.rglob('*'):
            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                files_to_process.append(str(file_path))

        stats.total = len(files_to_process)
        logger.info(f"Found {stats.total} files to process in {source_dir}")

        for i, file_path in enumerate(files_to_process):
            # Convert if needed
            if convert_formats and Path(file_path).suffix.lower() != self.MP3_EXTENSION:
                if dry_run:
                    logger.info(f"[DRY RUN] Would convert: {file_path}")
                else:
                    converted = self.convert_to_mp3(file_path, remove_source=True)
                    if converted:
                        file_path = converted
                    else:
                        stats.failed += 1
                        stats.results.append(ProcessingResult(
                            original_path=file_path,
                            status="failed",
                            error="Conversion failed"
                        ))
                        continue

            # Process file
            result = await self.process_file(
                file_path=file_path,
                output_dir=output_dir,
                write_tags=write_tags,
                rename=rename,
                rename_template=rename_template,
                organize=organize,
                overwrite_tags=overwrite_tags,
                skip_recognized=skip_recognized,
                dry_run=dry_run,
            )

            stats.results.append(result)
            stats.processed += 1

            if result.status == "success":
                stats.recognized += 1
            elif result.status == "failed":
                stats.failed += 1
            elif result.status == "skipped":
                stats.skipped += 1

            # Progress callback
            if progress_callback:
                progress_callback(i + 1, stats.total, result)

        logger.info(
            f"Processing complete: {stats.recognized}/{stats.processed} recognized "
            f"({stats.success_rate:.1f}%), {stats.skipped} skipped, {stats.failed} failed"
        )

        return stats


# ============================================================
# Convenience Functions
# ============================================================

async def recognize_and_tag(
        path: str,
        rename: bool = False,
        organize: bool = False,
        output_dir: Optional[str] = None,
) -> ProcessingStats:
    """
    Convenience function to recognize and tag music files.
    
    Args:
        path: File or directory path
        rename: Rename files to "Artist - Title.mp3"
        organize: Organize into Artist/Album folders
        output_dir: Output directory for organized files
    """
    recognizer = MusicRecognizer()

    if os.path.isfile(path):
        result = await recognizer.process_file(
            file_path=path,
            output_dir=output_dir,
            rename=rename,
            organize=organize,
        )
        stats = ProcessingStats(total=1, processed=1)
        stats.results.append(result)
        if result.status == "success":
            stats.recognized = 1
        elif result.status == "failed":
            stats.failed = 1
        return stats
    else:
        return await recognizer.process_directory(
            source_dir=path,
            output_dir=output_dir,
            rename=rename,
            organize=organize,
        )


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """Configure logging for the application."""
    handlers = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        handlers=handlers,
    )
