"""Tests for media upload methods: add_media, add_media_by_url, add_media_v2, upload_file."""

import io
import json
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest
import responses

from tests.conftest import HOST, SAMPLE_ITEM

UPLOAD_URL_PREFIX = HOST + "/items/uploadToReview/"

# Patch targets in the syncsketch module
OPEN_PATCH = "syncsketch.syncsketch.open"
STAT_PATCH = "syncsketch.syncsketch.os.stat"
MIMETYPES_PATCH = "syncsketch.syncsketch.mimetypes.guess_type"


def fake_open(data=b"fake file data"):
    """Return a callable that produces BytesIO objects (works both as direct call and context manager)."""

    def _open(*args, **kwargs):
        return io.BytesIO(data)

    return _open


class TestAddMedia:
    @responses.activate
    def test_add_media_basic(self, api):
        responses.add(responses.POST, UPLOAD_URL_PREFIX + "456/", json=SAMPLE_ITEM)

        with patch(OPEN_PATCH, side_effect=fake_open()):
            result = api.add_media(456, "/tmp/test.mp4", artist_name="Artist", file_name="test.mp4")

        assert result["id"] == 789

    @responses.activate
    def test_add_media_with_no_convert_flag(self, api):
        responses.add(responses.POST, UPLOAD_URL_PREFIX + "456/", json=SAMPLE_ITEM)

        with patch(OPEN_PATCH, side_effect=fake_open()):
            api.add_media(456, "/tmp/test.mp4", noConvertFlag=True)

        assert "noConvertFlag=1" in responses.calls[0].request.url

    @responses.activate
    def test_add_media_with_item_parent_id(self, api):
        responses.add(responses.POST, UPLOAD_URL_PREFIX + "456/", json=SAMPLE_ITEM)

        with patch(OPEN_PATCH, side_effect=fake_open()):
            api.add_media(456, "/tmp/test.mp4", itemParentId=10)

        assert "itemParentId=10" in responses.calls[0].request.url


class TestAddMediaByUrl:
    @responses.activate
    def test_add_media_by_url(self, api):
        responses.add(responses.POST, UPLOAD_URL_PREFIX + "456/", json=SAMPLE_ITEM)
        result = api.add_media_by_url(456, "https://example.com/video.mp4", artist_name="Artist")
        assert result["id"] == 789

    def test_missing_review_id_raises(self, api):
        with pytest.raises(Exception, match="review id"):
            api.add_media_by_url(None, "https://example.com/video.mp4")

    def test_missing_media_url_raises(self, api):
        with pytest.raises(Exception, match="media_url"):
            api.add_media_by_url(456, "")

    @responses.activate
    def test_with_no_convert_flag(self, api):
        responses.add(responses.POST, UPLOAD_URL_PREFIX + "456/", json=SAMPLE_ITEM)
        api.add_media_by_url(456, "https://example.com/v.mp4", noConvertFlag=True)
        assert "noConvertFlag=1" in responses.calls[0].request.url


class TestAddMediaV2:
    def test_no_header_auth_returns_none(self, api):
        result = api.add_media_v2(456, "/tmp/test.mp4")
        assert result is None

    @responses.activate
    @patch(MIMETYPES_PATCH, return_value=("video/mp4", None))
    @patch(STAT_PATCH)
    def test_large_file_delegates_to_v1(self, mock_stat, mock_mime, api_header):
        mock_stat.return_value = MagicMock(st_size=6_000_000)
        responses.add(responses.POST, UPLOAD_URL_PREFIX + "456/", json={"id": 10, "uuid": "abc"})

        with patch(OPEN_PATCH, side_effect=fake_open()):
            result = api_header.add_media_v2(456, "/tmp/test.mp4")
        assert result["id"] == 10
        assert result["uuid"] == "abc"

    @responses.activate
    @patch(MIMETYPES_PATCH, return_value=("video/mp4", None))
    @patch(STAT_PATCH)
    def test_small_file_s3_flow(self, mock_stat, mock_mime, api_header):
        mock_stat.return_value = MagicMock(st_size=1000)

        signed_url_response = {
            "url": "https://s3.amazonaws.com/bucket",
            "fields": {
                "key": "uploads/test.mp4",
                "x-amz-meta-item-id": "10",
                "x-amz-meta-item-uuid": "abc-123",
            },
        }
        responses.add(responses.POST, HOST + "/uploads/get-s3-signed-url/", json=signed_url_response)
        responses.add(responses.POST, "https://s3.amazonaws.com/bucket", status=204)

        with patch(OPEN_PATCH, side_effect=fake_open()):
            result = api_header.add_media_v2(456, "/tmp/test.mp4")

        assert result == {"id": "10", "uuid": "abc-123"}


class TestUploadFile:
    def test_no_header_auth_returns_none(self, api):
        result = api.upload_file(456, "/tmp/test.mp4")
        assert result is None

    @responses.activate
    @patch("time.sleep")
    @patch(MIMETYPES_PATCH, return_value=("video/mp4", None))
    @patch(STAT_PATCH)
    def test_success_flow(self, mock_stat, mock_mime, mock_sleep, api_header):
        mock_stat.return_value = MagicMock(st_size=100)

        # Step 1: start upload
        responses.add(
            responses.POST,
            HOST + "/uploads/stats/upload-start/",
            json={"item_id": 10, "item_uuid": "abc-123"},
        )
        # Step 2: init multipart
        responses.add(
            responses.POST,
            HOST + "/uploads/multipart-upload/",
            json={"uploadId": "upload-1", "key": "upload-key"},
        )
        # Step 3: sign part
        responses.add(
            responses.GET,
            HOST + "/uploads/multipart-upload/upload-1/sign-part/1/",
            json={"url": "https://s3.example.com/part1"},
        )
        # Upload part to S3
        responses.add(
            responses.PUT,
            "https://s3.example.com/part1",
            headers={"ETag": '"etag1"'},
            status=200,
        )
        # Step 5: complete multipart
        responses.add(
            responses.POST,
            HOST + "/uploads/multipart-upload/upload-1/complete/",
            json={"ok": True},
        )
        # Final: get_item
        responses.add(responses.GET, HOST + "/api/v1/item/10/", json=SAMPLE_ITEM)

        with patch(OPEN_PATCH, mock_open(read_data=b"chunk")):
            result = api_header.upload_file(456, "/tmp/test.mp4", max_workers=1)

        assert result["id"] == 789

    @responses.activate
    @patch(MIMETYPES_PATCH, return_value=("video/mp4", None))
    @patch(STAT_PATCH)
    def test_start_upload_failure(self, mock_stat, mock_mime, api_header):
        mock_stat.return_value = MagicMock(st_size=100)
        responses.add(
            responses.POST,
            HOST + "/uploads/stats/upload-start/",
            json={"error": "fail"},
            status=400,
        )
        with patch(OPEN_PATCH, mock_open(read_data=b"chunk")):
            result = api_header.upload_file(456, "/tmp/test.mp4", max_workers=1)
        assert result is None

    @responses.activate
    @patch(MIMETYPES_PATCH, return_value=("video/mp4", None))
    @patch(STAT_PATCH)
    def test_multipart_init_failure(self, mock_stat, mock_mime, api_header):
        mock_stat.return_value = MagicMock(st_size=100)
        responses.add(
            responses.POST,
            HOST + "/uploads/stats/upload-start/",
            json={"item_id": 10, "item_uuid": "abc"},
        )
        responses.add(
            responses.POST,
            HOST + "/uploads/multipart-upload/",
            json={"error": "fail"},
            status=400,
        )
        with patch(OPEN_PATCH, mock_open(read_data=b"chunk")):
            result = api_header.upload_file(456, "/tmp/test.mp4", max_workers=1)
        assert result is None
