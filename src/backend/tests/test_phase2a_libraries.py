"""
Tests for Phase 2A library implementations

Tests for:
- Video filename parser (guessit)
- SRT file handler (pysrt)
- Redis cache client
"""

import tempfile
from pathlib import Path

import pysrt
import pytest

from core.cache.redis_client import RedisCacheClient
from services.videoservice.srt_file_handler import SRTFileHandler
from services.videoservice.video_filename_parser import VideoFilenameParser


class TestVideoFilenameParser:
    """Test video filename parsing with guessit"""

    def test_parse_standard_season_episode_format(self):
        """Test parsing S##E## format"""
        parser = VideoFilenameParser()
        result = parser.parse("Breaking.Bad.S01E01.720p.mkv")

        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["quality"] == "720p"
        assert "Breaking Bad" in result["series"] or "Breaking" in result["series"]

    def test_parse_alternative_format(self):
        """Test parsing 1x01 format"""
        parser = VideoFilenameParser()
        result = parser.parse("The.Office.US.2x01.HDTV.x264")

        assert result["season"] == 2
        assert result["episode"] == 1
        assert "Office" in result["series"] or "office" in result["series"]

    def test_parse_episode_text_format(self):
        """Test parsing 'Episode N' format"""
        parser = VideoFilenameParser()
        result = parser.parse("Lost.Season.1.Episode.3")

        assert result["season"] == 1
        assert result["episode"] == 3

    def test_get_episode_number(self):
        """Test extracting episode number"""
        parser = VideoFilenameParser()
        episode = parser.get_episode_number("breaking.bad.s01e05.720p.mkv")
        assert episode == 5

    def test_get_season_number(self):
        """Test extracting season number"""
        parser = VideoFilenameParser()
        season = parser.get_season_number("breaking.bad.s03e12.720p.mkv")
        assert season == 3

    def test_is_valid_video(self):
        """Test video validation"""
        parser = VideoFilenameParser()

        # Valid videos
        assert parser.is_valid_video("show.s01e01.mkv") is True
        assert parser.is_valid_video("show.1x05.mkv") is True

        # Invalid videos (no episode info)
        assert parser.is_valid_video("random_file.mkv") is False


class TestSRTFileHandler:
    """Test SRT file handling with pysrt"""

    def test_create_subtitle(self):
        """Test creating subtitle item"""
        handler = SRTFileHandler()
        sub = handler.create_subtitle(1, 0, 5000, "Test subtitle")

        assert sub.index == 1
        assert sub.text == "Test subtitle"
        # pysrt stores time as SubRipTime objects, just verify they exist
        assert sub.start is not None
        assert sub.end is not None

    def test_write_and_read_srt(self):
        """Test writing and reading SRT file"""
        handler = SRTFileHandler()

        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as f:
            temp_path = f.name

        try:
            # Create subtitles
            subs = pysrt.SubRipFile()
            subs.append(handler.create_subtitle(1, 0, 5000, "First"))
            subs.append(handler.create_subtitle(2, 5000, 10000, "Second"))

            # Write
            assert handler.write_srt(temp_path, subs) is True

            # Read back
            loaded = handler.read_srt(temp_path)
            assert loaded is not None
            assert len(loaded) == 2
            assert loaded[0].text == "First"
            assert loaded[1].text == "Second"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_extract_text(self):
        """Test extracting text from subtitles"""
        handler = SRTFileHandler()

        subs = pysrt.SubRipFile()
        subs.append(handler.create_subtitle(1, 0, 5000, "Hello world"))
        subs.append(handler.create_subtitle(2, 5000, 10000, "Goodbye world"))

        text = handler.extract_text(subs)
        assert "Hello world" in text
        assert "Goodbye world" in text

    def test_get_duration(self):
        """Test getting subtitle duration"""
        handler = SRTFileHandler()

        subs = pysrt.SubRipFile()
        subs.append(handler.create_subtitle(1, 0, 5000, "Text"))
        subs.append(handler.create_subtitle(2, 5000, 15000, "More text"))

        duration = handler.get_duration(subs)
        assert duration == 15000


class TestRedisCacheClient:
    """Test Redis cache client"""

    @pytest.mark.asyncio
    async def test_cache_connection(self):
        """Test Redis connection"""
        client = RedisCacheClient()
        # Just check if it initializes (may or may not connect depending on Redis availability)
        assert client.host == "localhost"
        assert client.port == 6379

    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        """Test setting and getting cache values"""
        client = RedisCacheClient()

        if not client.is_connected():
            pytest.skip("Redis not available")

        # Set value
        success = await client.set("test_key", {"message": "hello"})
        assert success is True

        # Get value
        value = await client.get("test_key")
        assert value is not None
        assert value["message"] == "hello"

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """Test deleting cache values"""
        client = RedisCacheClient()

        if not client.is_connected():
            pytest.skip("Redis not available")

        # Set and delete
        await client.set("delete_test", "value")
        success = await client.delete("delete_test")

        # Verify deleted
        value = await client.get("delete_test")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_invalidate_pattern(self):
        """Test pattern-based cache invalidation"""
        client = RedisCacheClient()

        if not client.is_connected():
            pytest.skip("Redis not available")

        # Set multiple values
        await client.set("vocab:de:hallo", {"word": "hallo"})
        await client.set("vocab:de:welt", {"word": "welt"})
        await client.set("other:key", {"data": "value"})

        # Invalidate vocab keys
        deleted = await client.invalidate_pattern("vocab:*")
        assert deleted > 0


# Integration test
class TestPhase2AIntegration:
    """Integration tests for Phase 2A libraries"""

    def test_guessit_handles_complex_filenames(self):
        """Test guessit with real-world complex filenames"""
        parser = VideoFilenameParser()

        complex_files = [
            "game.of.thrones.s08e06.1080p.web-dl.aac2.0.h.264.mkv",
            "The.Crown.2016.S04E10.720p.NF.WEBRip.AAC2.0.x264.mkv",
            "Friends.Season.5.Episode.7.The.One.Where.Phoebe.Hides.Her.Pregnancy.HDTV.x264.mkv",
        ]

        for filename in complex_files:
            result = parser.parse(filename)
            # Should always extract episode number
            assert result["episode"] is not None, f"Failed to parse: {filename}"

    @pytest.mark.asyncio
    async def test_redis_caching_workflow(self):
        """Test typical caching workflow"""
        client = RedisCacheClient()

        if not client.is_connected():
            pytest.skip("Redis not available")

        # Simulate vocabulary lookup caching
        word_data = {"word": "hallo", "translation": "hello", "level": "A1", "lemma": "hallo"}

        # Cache key
        cache_key = "vocab:de:hallo"

        # Set cache
        await client.set(cache_key, word_data, ttl=3600)

        # Retrieve from cache
        cached = await client.get(cache_key)
        assert cached == word_data

        # Clean up
        await client.delete(cache_key)
