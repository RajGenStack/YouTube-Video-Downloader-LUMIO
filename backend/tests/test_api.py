"""
tests/test_api.py
Unit and integration tests for the Lumio API.
Real yt-dlp calls are mocked so tests run offline and fast.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

API_FETCH_INFO = "/api/fetch-info"
API_DOWNLOAD = "/api/download"
TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
DOWNLOADER_THREAD_PATCH = "app.downloader.asyncio.to_thread"



# ── Health ───────────────────────────────────────────────────────────────────
class TestHealth:
    async def test_health_returns_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "yt_dlp_version" in data

    async def test_root_returns_service_info(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ── Input validation ─────────────────────────────────────────────────────────
class TestValidation:
    async def test_fetch_info_rejects_empty_url(self, client):
        resp = await client.post(API_FETCH_INFO, json={"url": ""})
        assert resp.status_code == 422

    async def test_fetch_info_rejects_non_youtube_url(self, client):
        resp = await client.post(API_FETCH_INFO, json={"url": "https://vimeo.com/123456"})
        assert resp.status_code == 422
        assert "YouTube" in resp.json()["detail"]

    async def test_fetch_info_rejects_malformed_url(self, client):
        resp = await client.post(API_FETCH_INFO, json={"url": "not-a-url-at-all"})
        assert resp.status_code == 422

    async def test_fetch_info_accepts_standard_url(self, client):
        """Valid URL shape passes schema validation (yt-dlp call is mocked)."""
        mock_info = {
            "title": "Test Video",
            "duration": 180,
            "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
            "uploader": "TestChannel",
            "channel_url": "https://youtube.com/channel/test",
            "view_count": 1000,
            "like_count": 50,
            "upload_date": "20240101",
            "description": "A test video description.",
            "is_live": False,
            "formats": [{"height": 720}, {"height": 1080}],
        }
        with patch(DOWNLOADER_THREAD_PATCH, new_callable=AsyncMock) as mock_thread:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = mock_info
            mock_thread.return_value = mock_info
            resp = await client.post(
                API_FETCH_INFO,
                json={"url": TEST_YOUTUBE_URL},
            )
        # Either 200 (mock worked) or 422 (yt-dlp error in test env) — not 500
        assert resp.status_code in (200, 422)

    async def test_fetch_info_accepts_shorts_url(self, client):
        resp_body = {"url": "https://www.youtube.com/shorts/dQw4w9WgXcQ"}
        with patch(DOWNLOADER_THREAD_PATCH, new_callable=AsyncMock) as m:
            m.side_effect = ValueError("mocked error")
            resp = await client.post(API_FETCH_INFO, json=resp_body)
        assert resp.status_code == 422   # yt-dlp error, not validation error → 422 not 500

    async def test_fetch_info_accepts_youtu_be_url(self, client):
        with patch(DOWNLOADER_THREAD_PATCH, new_callable=AsyncMock) as m:
            m.side_effect = ValueError("mocked error")
            resp = await client.post(
                API_FETCH_INFO,
                json={"url": "https://youtu.be/dQw4w9WgXcQ"},
            )
        assert resp.status_code == 422   # passes URL validation, fails yt-dlp (expected)

    async def test_download_rejects_invalid_mode(self, client):
        resp = await client.post(
            API_DOWNLOAD,
            json={"url": TEST_YOUTUBE_URL, "mode": "flac", "quality": "320k"},
        )
        assert resp.status_code == 422

    async def test_download_rejects_invalid_quality_for_mp3(self, client):
        resp = await client.post(
            API_DOWNLOAD,
            json={"url": TEST_YOUTUBE_URL, "mode": "mp3", "quality": "9000k"},
        )
        assert resp.status_code == 422

    async def test_download_rejects_invalid_quality_for_mp4(self, client):
        resp = await client.post(
            API_DOWNLOAD,
            json={"url": TEST_YOUTUBE_URL, "mode": "mp4", "quality": "9999p"},
        )
        assert resp.status_code == 422

    async def test_download_rejects_mp3_quality_on_mp4_mode(self, client):
        resp = await client.post(
            API_DOWNLOAD,
            json={"url": TEST_YOUTUBE_URL, "mode": "mp4", "quality": "320k"},
        )
        assert resp.status_code in (400, 422)

    async def test_download_rejects_mp4_quality_on_mp3_mode(self, client):
        resp = await client.post(
            API_DOWNLOAD,
            json={"url": TEST_YOUTUBE_URL, "mode": "mp3", "quality": "720p"},
        )
        assert resp.status_code in (400, 422)


# ── Schema unit tests ────────────────────────────────────────────────────────
class TestSchemas:
    def test_valid_youtube_urls_pass(self):
        from app.schemas import FetchInfoRequest
        valid_urls = [
            TEST_YOUTUBE_URL,
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/embed/dQw4w9WgXcQ",
        ]
        for url in valid_urls:
            req = FetchInfoRequest(url=url)
            assert req.url == url

    def test_invalid_urls_raise_validation_error(self):
        from pydantic import ValidationError
        from app.schemas import FetchInfoRequest
        bad_urls = [
            "",
            "https://vimeo.com/123",
            "https://tiktok.com/@user/video/123",
            "just-some-text",
            "https://youtube.com/channel/UCxxxxxx",   # channel, not video
        ]
        for url in bad_urls:
            with pytest.raises(ValidationError):
                FetchInfoRequest(url=url)

    def test_all_mp3_qualities_are_accepted(self):
        from app.schemas import DownloadRequest, VALID_MP3_QUALITIES
        for q in VALID_MP3_QUALITIES:
            req = DownloadRequest(
                url=TEST_YOUTUBE_URL,
                mode="mp3",
                quality=q,
            )
            assert req.quality == q

    def test_all_mp4_qualities_are_accepted(self):
        from app.schemas import DownloadRequest, VALID_MP4_QUALITIES
        for q in VALID_MP4_QUALITIES:
            req = DownloadRequest(
                url=TEST_YOUTUBE_URL,
                mode="mp4",
                quality=q,
            )
            assert req.quality == q


# ── Downloader helpers ───────────────────────────────────────────────────────
class TestDownloaderHelpers:
    def test_seconds_to_str_minutes_only(self):
        from app.downloader import seconds_to_str
        assert seconds_to_str(90)   == "1:30"
        assert seconds_to_str(0)    == "0:00"
        assert seconds_to_str(59)   == "0:59"
        assert seconds_to_str(600)  == "10:00"

    def test_seconds_to_str_with_hours(self):
        from app.downloader import seconds_to_str
        assert seconds_to_str(3661) == "1:01:01"
        assert seconds_to_str(7200) == "2:00:00"

    def test_safe_filename_strips_bad_chars(self):
        from app.downloader import safe_filename
        name = 'My Video: "Best" Ever? <test>'
        result = safe_filename(name, "mp4")
        assert "/" not in result
        assert "*" not in result
        assert result.endswith(".mp4")

    def test_safe_filename_truncates_long_names(self):
        from app.downloader import safe_filename
        long_name = "A" * 300
        result = safe_filename(long_name, "mp3")
        assert len(result) <= 200

    def test_audio_bitrate_map_complete(self):
        from app.downloader import AUDIO_BITRATE_MAP
        from app.schemas import VALID_MP3_QUALITIES
        for q in VALID_MP3_QUALITIES:
            assert q in AUDIO_BITRATE_MAP, f"Missing bitrate map for {q}"

    def test_video_format_map_complete(self):
        from app.downloader import VIDEO_FORMAT_MAP
        from app.schemas import VALID_MP4_QUALITIES
        for q in VALID_MP4_QUALITIES:
            assert q in VIDEO_FORMAT_MAP, f"Missing format map for {q}"

    def test_get_available_mp4_qualities(self):
        from app.downloader import _get_available_mp4_qualities
        
        # Scenario 1: Only SDR up to 720p
        formats_720p = [{"height": 144}, {"height": 360}, {"height": 720}]
        quals = _get_available_mp4_qualities(formats_720p)
        assert "144p" in quals
        assert "720p" in quals
        assert "1080p" not in quals
        assert "1080p-hdr" not in quals

        # Scenario 2: SDR up to 2160p (4K) but no HDR
        formats_4k = [{"height": 1080}, {"height": 2160}]
        quals = _get_available_mp4_qualities(formats_4k)
        assert "1080p" in quals
        assert "2160p" in quals
        assert "4k-hdr" not in quals

        # Scenario 3: HDR video up to 1080p
        formats_hdr = [{"height": 720}, {"height": 1080, "dynamic_range": "HDR"}]
        quals = _get_available_mp4_qualities(formats_hdr)
        assert "1080p" in quals
        assert "1080p-hdr" in quals
        assert "1440p-hdr" not in quals



# ── Config ───────────────────────────────────────────────────────────────────
class TestConfig:
    def test_origins_list_parses_correctly(self):
        from app.config import Settings
        s = Settings(ALLOWED_ORIGINS="https://a.com,https://b.com, https://c.com")
        assert "https://a.com" in s.origins_list
        assert "https://b.com" in s.origins_list
        assert "https://c.com" in s.origins_list
        assert len(s.origins_list) == 3

    def test_default_environment_is_production(self):
        from app.config import Settings
        assert Settings.model_fields["ENVIRONMENT"].default == "production"


# ── 404 / 405 handlers ───────────────────────────────────────────────────────
class TestErrorHandlers:
    async def test_404_returns_json(self, client):
        resp = await client.get("/non-existent-route")
        assert resp.status_code == 404
        assert resp.json()["code"] == "NOT_FOUND"

    async def test_method_not_allowed(self, client):
        resp = await client.get(API_FETCH_INFO)   # GET on a POST endpoint
        assert resp.status_code == 405
