"""Tests for comments, annotations, and grease pencil overlays."""

import json
import os
from unittest.mock import mock_open, patch

import responses

from tests.conftest import HOST, SAMPLE_ITEM, make_list_response


class TestAddComment:
    @responses.activate
    def test_add_comment(self, api):
        # get_item call
        responses.add(responses.GET, HOST + "/api/v1/item/789/", json=SAMPLE_ITEM)
        # post frame
        frame_data = {"id": 1, "text": "Great work!"}
        responses.add(responses.POST, HOST + "/api/v1/frame/", json=frame_data)

        result = api.add_comment(789, "Great work!", 456, frame=5)
        assert result["text"] == "Great work!"

        # Verify the POST body
        body = json.loads(responses.calls[1].request.body)
        assert body["item"] == "/api/v1/item/789/"
        assert body["frame"] == 5
        assert body["revision"] == "/api/v1/revision/101/"
        assert body["type"] == "comment"
        assert body["text"] == "Great work!"

    @responses.activate
    def test_no_revision_id_returns_error(self, api):
        item_no_revision = {"id": 789, "name": "test.mp4"}
        responses.add(responses.GET, HOST + "/api/v1/item/789/", json=item_no_revision)
        result = api.add_comment(789, "text", 456)
        assert result == "error"


class TestGetAnnotations:
    @responses.activate
    def test_get_annotations(self, api):
        responses.add(responses.GET, HOST + "/api/v1/frame/", json=make_list_response([{"id": 1}]))
        api.get_annotations(789)
        params = responses.calls[0].request.params
        assert params["item__id"] == "789"
        assert params["active"] == "1"

    @responses.activate
    def test_with_revision_id(self, api):
        responses.add(responses.GET, HOST + "/api/v1/frame/", json=make_list_response([]))
        api.get_annotations(789, revisionId=101)
        assert responses.calls[0].request.params["revision__id"] == "101"

    @responses.activate
    def test_with_review_id(self, api):
        responses.add(responses.GET, HOST + "/api/v1/frame/", json=make_list_response([]))
        api.get_annotations(789, review_id=456)
        assert responses.calls[0].request.params["revision__review_id"] == "456"


class TestGetFlattenedAnnotations:
    @responses.activate
    @patch("time.sleep")
    def test_success(self, mock_sleep, api):
        flattened_url = HOST + "/api/v2/downloads/flattenedSketches/456/789/"
        # POST to start celery task
        responses.add(responses.POST, flattened_url, json="task-id-123")
        # First GET: processing
        check_url = HOST + "/api/v2/downloads/flattenedSketches/task-id-123/"
        responses.add(responses.GET, check_url, json={"status": "processing"})
        # Second GET: done
        responses.add(responses.GET, check_url, json={"status": "done", "data": ["sketch1.png"]})

        result = api.get_flattened_annotations(456, 789)
        assert result["status"] == "done"

    @responses.activate
    def test_failed(self, api):
        flattened_url = HOST + "/api/v2/downloads/flattenedSketches/456/789/"
        responses.add(responses.POST, flattened_url, json="task-id-123")
        check_url = HOST + "/api/v2/downloads/flattenedSketches/task-id-123/"
        responses.add(responses.GET, check_url, json={"status": "failed"})

        result = api.get_flattened_annotations(456, 789)
        assert result is None


class TestGetGreasePencilOverlays:
    @responses.activate
    @patch("time.sleep")
    def test_success(self, mock_sleep, api):
        gp_url = HOST + "/api/v2/downloads/greasePencil/456/789/"
        responses.add(responses.POST, gp_url, json="task-id-456")

        check_url = HOST + "/api/v2/downloads/greasePencil/task-id-456/"
        responses.add(
            responses.GET,
            check_url,
            json={
                "status": "done",
                "data": {"fileName": "overlay", "s3Path": "https://s3.example.com/overlay.zip"},
            },
        )
        responses.add(responses.GET, "https://s3.example.com/overlay.zip", body=b"zipdata")

        m = mock_open()
        with patch("syncsketch.syncsketch.open", m):
            result = api.get_grease_pencil_overlays(456, 789)

        assert result == "/tmp/overlay.zip"
        m.assert_called_once_with("/tmp/overlay.zip", "wb")

    @responses.activate
    def test_failed(self, api):
        gp_url = HOST + "/api/v2/downloads/greasePencil/456/789/"
        responses.add(responses.POST, gp_url, json="task-id-456")
        check_url = HOST + "/api/v2/downloads/greasePencil/task-id-456/"
        responses.add(responses.GET, check_url, json={"status": "failed"})

        result = api.get_grease_pencil_overlays(456, 789)
        assert result is False

    @responses.activate
    @patch("time.sleep")
    def test_custom_homedir(self, mock_sleep, api):
        gp_url = HOST + "/api/v2/downloads/greasePencil/456/789/"
        responses.add(responses.POST, gp_url, json="task-id-456")
        check_url = HOST + "/api/v2/downloads/greasePencil/task-id-456/"
        responses.add(
            responses.GET,
            check_url,
            json={
                "status": "done",
                "data": {"fileName": "overlay", "s3Path": "https://s3.example.com/overlay.zip"},
            },
        )
        responses.add(responses.GET, "https://s3.example.com/overlay.zip", body=b"zipdata")

        m = mock_open()
        with patch("syncsketch.syncsketch.open", m):
            result = api.get_grease_pencil_overlays(456, 789, homedir="/custom/path")

        expected_path = os.path.join("/custom/path", "overlay.zip")
        assert result == expected_path
