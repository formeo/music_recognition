"""
Tests for Music Recognition

Run with: pytest -v
"""

import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from music_recognition import (
    MusicRecognizer,
    TrackInfo,
    ProcessingResult,
    ProcessingStats,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def recognizer():
    """Create a MusicRecognizer instance."""
    return MusicRecognizer(max_concurrent=2, delay_between_requests=0,use_cache=False,cache_path=None)


@pytest.fixture
def sample_track_info():
    """Sample recognized track info."""
    return TrackInfo(
        title="Bohemian Rhapsody",
        artist="Queen",
        album="A Night at the Opera",
        year="1975",
        genre="Rock",
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath)


@pytest.fixture
def sample_shazam_response():
    """Sample Shazam API response."""
    return {
        "track": {
            "title": "Bohemian Rhapsody",
            "subtitle": "Queen",
            "key": "12345",
            "sections": [
                {
                    "type": "SONG",
                    "metadata": [
                        {"title": "Album", "text": "A Night at the Opera"},
                        {"title": "Released", "text": "1975"},
                    ]
                }
            ],
            "images": {
                "coverart": "https://example.com/cover.jpg"
            },
            "hub": {
                "options": [
                    {"listcaption": "Rock"}
                ]
            }
        }
    }


# ============================================================
# TrackInfo Tests
# ============================================================

class TestTrackInfo:
    """Tests for TrackInfo dataclass."""
    
    def test_is_recognized_true(self, sample_track_info):
        """Test is_recognized returns True for valid data."""
        assert sample_track_info.is_recognized is True
    
    def test_is_recognized_false_unknown_title(self):
        """Test is_recognized returns False for unknown title."""
        info = TrackInfo(title="Unknown", artist="Queen")
        assert info.is_recognized is False
    
    def test_is_recognized_false_unknown_artist(self):
        """Test is_recognized returns False for unknown artist."""
        info = TrackInfo(title="Song", artist="Unknown")
        assert info.is_recognized is False
    
    def test_is_recognized_false_both_unknown(self):
        """Test is_recognized returns False when both are unknown."""
        info = TrackInfo()
        assert info.is_recognized is False
    
    def test_to_dict(self, sample_track_info):
        """Test conversion to dictionary."""
        d = sample_track_info.to_dict()
        
        assert d["title"] == "Bohemian Rhapsody"
        assert d["artist"] == "Queen"
        assert d["album"] == "A Night at the Opera"
        assert d["recognized"] is True


# ============================================================
# ProcessingStats Tests
# ============================================================

class TestProcessingStats:
    """Tests for ProcessingStats."""
    
    def test_success_rate_zero_processed(self):
        """Test success rate when nothing processed."""
        stats = ProcessingStats()
        assert stats.success_rate == 0.0
    
    def test_success_rate_all_recognized(self):
        """Test success rate when all files recognized."""
        stats = ProcessingStats(processed=10, recognized=10)
        assert stats.success_rate == 100.0
    
    def test_success_rate_partial(self):
        """Test success rate for partial recognition."""
        stats = ProcessingStats(processed=10, recognized=7)
        assert stats.success_rate == 70.0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = ProcessingStats(
            total=10,
            processed=8,
            recognized=6,
            failed=2,
            skipped=2,
        )
        d = stats.to_dict()
        
        assert d["total"] == 10
        assert d["processed"] == 8
        assert d["recognized"] == 6
        assert d["failed"] == 2
        assert d["skipped"] == 2
        assert d["success_rate"] == 75.0


# ============================================================
# MusicRecognizer Tests
# ============================================================

class TestMusicRecognizer:
    """Tests for MusicRecognizer."""
    
    def test_sanitize_filename_basic(self, recognizer):
        """Test basic filename sanitization."""
        assert recognizer.sanitize_filename("Song Title") == "Song Title"
    
    def test_sanitize_filename_forbidden_chars(self, recognizer):
        """Test removal of forbidden characters."""
        assert recognizer.sanitize_filename("Song: Title/Artist") == "Song_ Title_Artist"
        assert recognizer.sanitize_filename("Track <1>") == "Track _1_"
        assert recognizer.sanitize_filename('Say "Hello"') == "Say _Hello_"
    
    def test_sanitize_filename_strips_spaces(self, recognizer):
        """Test stripping of leading/trailing spaces."""
        assert recognizer.sanitize_filename("  Song  ") == "Song"
    
    def test_sanitize_filename_strips_dots(self, recognizer):
        """Test stripping of leading/trailing dots."""
        assert recognizer.sanitize_filename("...Song...") == "Song"
    
    def test_sanitize_filename_empty_returns_unknown(self, recognizer):
        """Test empty string returns Unknown."""
        assert recognizer.sanitize_filename("") == "Unknown"
        assert recognizer.sanitize_filename("...") == "Unknown"
    
    def test_sanitize_filename_long_name(self, recognizer):
        """Test truncation of long names."""
        long_name = "A" * 300
        result = recognizer.sanitize_filename(long_name)
        assert len(result) <= 200
    
    def test_generate_filename_default_template(self, recognizer, sample_track_info):
        """Test filename generation with default template."""
        filename = recognizer.generate_filename(sample_track_info)
        assert filename == "Queen - Bohemian Rhapsody.mp3"
    
    def test_generate_filename_custom_template(self, recognizer, sample_track_info):
        """Test filename generation with custom template."""
        template = "{artist}/{album}/{title}.mp3"
        filename = recognizer.generate_filename(sample_track_info, template)
        assert filename == "Queen/A Night at the Opera/Bohemian Rhapsody.mp3"
    
    def test_generate_filename_with_year(self, recognizer, sample_track_info):
        """Test filename generation with year placeholder."""
        template = "{artist} - {title} ({year}).mp3"
        filename = recognizer.generate_filename(sample_track_info, template)
        assert filename == "Queen - Bohemian Rhapsody (1975).mp3"
    
    def test_uniquify_new_file(self, recognizer, temp_dir):
        """Test uniquify with non-existing file."""
        path = os.path.join(temp_dir, "song.mp3")
        assert recognizer.uniquify(path) == path
    
    def test_uniquify_existing_file(self, recognizer, temp_dir):
        """Test uniquify with existing file."""
        path = os.path.join(temp_dir, "song.mp3")
        
        # Create the file
        Path(path).touch()
        
        result = recognizer.uniquify(path)
        assert result == os.path.join(temp_dir, "song (1).mp3")
    
    def test_uniquify_multiple_existing(self, recognizer, temp_dir):
        """Test uniquify with multiple existing files."""
        base_path = os.path.join(temp_dir, "song.mp3")
        
        # Create multiple files
        Path(base_path).touch()
        Path(os.path.join(temp_dir, "song (1).mp3")).touch()
        Path(os.path.join(temp_dir, "song (2).mp3")).touch()
        
        result = recognizer.uniquify(base_path)
        assert result == os.path.join(temp_dir, "song (3).mp3")
    
    def test_parse_shazam_response_valid(self, recognizer, sample_shazam_response):
        """Test parsing valid Shazam response."""
        info = recognizer._parse_shazam_response(sample_shazam_response)
        
        assert info.title == "Bohemian Rhapsody"
        assert info.artist == "Queen"
        assert info.album == "A Night at the Opera"
        assert info.year == "1975"
        assert info.cover_url == "https://example.com/cover.jpg"
        assert info.is_recognized is True
    
    def test_parse_shazam_response_empty(self, recognizer):
        """Test parsing empty Shazam response."""
        info = recognizer._parse_shazam_response({})
        assert info.is_recognized is False
    
    def test_parse_shazam_response_no_track(self, recognizer):
        """Test parsing response without track."""
        info = recognizer._parse_shazam_response({"matches": []})
        assert info.is_recognized is False


# ============================================================
# Async Tests
# ============================================================

class TestAsyncRecognition:
    """Tests for async recognition functionality."""
    
    @pytest.mark.asyncio
    async def test_recognize_file_success(self, recognizer, sample_shazam_response):
        """Test successful file recognition."""
        with patch.object(recognizer.shazam, 'recognize', new_callable=AsyncMock) as mock:
            mock.return_value = sample_shazam_response
            
            info = await recognizer.recognize_file("test.mp3")
            
            assert info.is_recognized is True
            assert info.title == "Bohemian Rhapsody"
            assert info.artist == "Queen"
    
    @pytest.mark.asyncio
    async def test_recognize_file_not_found(self, recognizer):
        """Test recognition when Shazam returns empty response."""
        with patch.object(recognizer.shazam, 'recognize', new_callable=AsyncMock) as mock:
            mock.return_value = {}
            
            info = await recognizer.recognize_file("test.mp3")
            
            assert info.is_recognized is False
    
    @pytest.mark.asyncio
    async def test_recognize_file_error_retry(self, recognizer, sample_shazam_response):
        """Test retry on recognition error."""
        with patch.object(recognizer.shazam, 'recognize', new_callable=AsyncMock) as mock:
            # First call fails, second succeeds
            mock.side_effect = [Exception("API Error"), sample_shazam_response]
            
            info = await recognizer.recognize_file("test.mp3")
            
            assert info.is_recognized is True
            assert mock.call_count == 2
    
    @pytest.mark.asyncio
    async def test_recognize_file_all_retries_fail(self, recognizer):
        """Test behavior when all retries fail."""
        recognizer.retry_attempts = 1
        
        with patch.object(recognizer.shazam, 'recognize', new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("API Error")
            
            info = await recognizer.recognize_file("test.mp3")
            
            assert info.is_recognized is False
            assert mock.call_count == 2  # Initial + 1 retry


# ============================================================
# Integration Tests
# ============================================================

class TestIntegration:
    """Integration tests (require more setup)."""
    
    def test_has_valid_tags_no_file(self, recognizer):
        """Test has_valid_tags with non-existing file."""
        result = recognizer.has_valid_tags("/nonexistent/file.mp3")
        assert result is False
    
    def test_read_existing_tags_no_file(self, recognizer):
        """Test read_existing_tags with non-existing file."""
        info = recognizer.read_existing_tags("/nonexistent/file.mp3")
        assert info.is_recognized is False


# ============================================================
# CLI Tests
# ============================================================

class TestCLI:
    """Tests for CLI functionality."""
    
    def test_import_cli(self):
        """Test CLI module can be imported."""
        from music_recognition.cli import main, Colors
        assert callable(main)
    
    def test_colors_defined(self):
        """Test color codes are defined."""
        from music_recognition.cli import Colors
        assert hasattr(Colors, 'GREEN')
        assert hasattr(Colors, 'RED')
        assert hasattr(Colors, 'END')


# ============================================================
# Run tests
# ============================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
