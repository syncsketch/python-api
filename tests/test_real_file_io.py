"""Tests using real temporary files to exercise os.stat, mimetypes.guess_type, and io.open
across Python versions. Only HTTP calls are mocked."""

import json
import os
import tempfile

import responses

from tests.conftest import HOST, SAMPLE_ITEM


def _make_temp_file(suffix=".mp4", content=b"fake video content", size=None):
    """Create a real temp file. If size is given, write exactly that many bytes."""
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    if size is not None:
        f.write(b"\x00" * size)
    else:
        f.write(content)
    f.close()
    return f.name


class TestAddMediaRealFile:
    @responses.activate
    def test_upload_real_file(self, api):
        filepath = _make_temp_file(suffix=".mp4")
        try:
            responses.add(
                responses.POST,
                HOST + "/items/uploadToReview/456/",
                json=SAMPLE_ITEM,
            )
            result = api.add_media(456, filepath, artist_name="Artist", file_name="test.mp4")
            assert result["id"] == 789
            # Verify the file was actually read and sent as multipart
            assert responses.calls[0].request.body is not None
        finally:
            os.unlink(filepath)

    @responses.activate
    def test_various_extensions(self, api):
        """Verify mimetypes.guess_type works for common media types across Python versions."""
        for suffix in [".mp4", ".mov", ".png", ".jpg", ".webm", ".pdf"]:
            filepath = _make_temp_file(suffix=suffix, content=b"data")
            try:
                responses.add(
                    responses.POST,
                    HOST + "/items/uploadToReview/456/",
                    json=SAMPLE_ITEM,
                )
                result = api.add_media(456, filepath)
                assert result is not None
            finally:
                os.unlink(filepath)


class TestAddMediaV2RealFile:
    @responses.activate
    def test_small_file_real_io(self, api_header):
        """Exercise os.stat and mimetypes.guess_type with a real small file."""
        filepath = _make_temp_file(suffix=".mp4", size=1000)
        try:
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

            result = api_header.add_media_v2(456, filepath)
            assert result == {"id": "10", "uuid": "abc-123"}

            # Verify os.stat was used correctly — the signed URL request should contain the real size
            body = json.loads(responses.calls[0].request.body)
            assert body["item_data"]["content_length"] == 1000
            assert body["item_data"]["content_type"] is not None
        finally:
            os.unlink(filepath)

    @responses.activate
    def test_large_file_falls_back_to_v1(self, api_header):
        """Files > 5MB should fall back to add_media_v1 (direct upload)."""
        filepath = _make_temp_file(suffix=".mp4", size=6_000_000)
        try:
            responses.add(
                responses.POST,
                HOST + "/items/uploadToReview/456/",
                json={"id": 10, "uuid": "abc"},
            )
            result = api_header.add_media_v2(456, filepath)
            assert result["id"] == 10
        finally:
            os.unlink(filepath)

    @responses.activate
    def test_file_name_passed_as_is(self, api_header):
        """add_media_v2 passes file_name directly without appending extension."""
        filepath = _make_temp_file(suffix=".webm", size=500)
        try:
            signed_url_response = {
                "url": "https://s3.amazonaws.com/bucket",
                "fields": {
                    "key": "uploads/test.webm",
                    "x-amz-meta-item-id": "10",
                    "x-amz-meta-item-uuid": "abc-123",
                },
            }
            responses.add(responses.POST, HOST + "/uploads/get-s3-signed-url/", json=signed_url_response)
            responses.add(responses.POST, "https://s3.amazonaws.com/bucket", status=204)

            result = api_header.add_media_v2(456, filepath, file_name="my_video")
            assert result is not None

            body = json.loads(responses.calls[0].request.body)
            # add_media_v2 does NOT append extension (unlike upload_file)
            assert body["item_name"] == "my_video"
        finally:
            os.unlink(filepath)


class TestUploadFileRealFile:
    @responses.activate
    def test_multipart_upload_real_file(self, api_header):
        """Full multipart upload flow with a real file — exercises open, os.stat, mimetypes."""
        filepath = _make_temp_file(suffix=".mp4", size=100)
        try:
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

            result = api_header.upload_file(456, filepath, max_workers=1)
            assert result["id"] == 789

            # Verify the start-upload request has correct file metadata
            start_body = json.loads(responses.calls[0].request.body)
            assert start_body["item_data"]["size"] == 100
            assert start_body["item_data"]["content_type"] is not None

            # Verify the actual file content was uploaded to S3
            s3_body = responses.calls[3].request.body
            assert len(s3_body) == 100
        finally:
            os.unlink(filepath)

    @responses.activate
    def test_chunking_with_multiple_parts(self, api_header):
        """Verify file is split into correct number of chunks."""
        # 15 bytes with chunk_size=5 = 3 parts
        filepath = _make_temp_file(suffix=".mp4", size=15)
        try:
            responses.add(
                responses.POST,
                HOST + "/uploads/stats/upload-start/",
                json={"item_id": 10, "item_uuid": "abc-123"},
            )
            responses.add(
                responses.POST,
                HOST + "/uploads/multipart-upload/",
                json={"uploadId": "upload-1", "key": "upload-key"},
            )
            # 3 sign-part + 3 S3 PUT calls
            for i in range(1, 4):
                responses.add(
                    responses.GET,
                    HOST + "/uploads/multipart-upload/upload-1/sign-part/%d/" % i,
                    json={"url": "https://s3.example.com/part%d" % i},
                )
                responses.add(
                    responses.PUT,
                    "https://s3.example.com/part%d" % i,
                    headers={"ETag": '"etag%d"' % i},
                    status=200,
                )
            responses.add(
                responses.POST,
                HOST + "/uploads/multipart-upload/upload-1/complete/",
                json={"ok": True},
            )
            responses.add(responses.GET, HOST + "/api/v1/item/10/", json=SAMPLE_ITEM)

            result = api_header.upload_file(456, filepath, chunk_size=5, max_workers=1)
            assert result["id"] == 789

            # Verify complete request has 3 parts
            complete_body = json.loads(responses.calls[8].request.body)
            assert len(complete_body["parts"]) == 3
            for i, part in enumerate(complete_body["parts"], 1):
                assert part["PartNumber"] == i
        finally:
            os.unlink(filepath)


class TestOsStatBehavior:
    def test_stat_returns_correct_size(self):
        """Verify os.stat works consistently across Python versions."""
        for size in [0, 1, 1024, 5 * 1024 * 1024]:
            filepath = _make_temp_file(size=size)
            try:
                assert os.stat(filepath).st_size == size
            finally:
                os.unlink(filepath)


class TestMimetypesConsistency:
    def test_common_media_types(self):
        """Verify mimetypes.guess_type returns expected types across Python versions."""
        import mimetypes

        expected = {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webm": "video/webm",
            ".pdf": "application/pdf",
            ".gif": "image/gif",
        }
        for ext, expected_type in expected.items():
            filepath = _make_temp_file(suffix=ext, content=b"x")
            try:
                guessed = mimetypes.guess_type(filepath, strict=False)[0]
                assert guessed == expected_type, "Expected %s for %s, got %s" % (expected_type, ext, guessed)
            finally:
                os.unlink(filepath)
