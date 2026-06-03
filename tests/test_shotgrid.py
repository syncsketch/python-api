"""Tests for Shotgrid integration methods."""

import json

import pytest
import responses

from tests.conftest import HOST


class TestShotgridCreateConfig:
    @responses.activate
    def test_success(self, api):
        data = {"url": "https://sg.example.com", "username": "script_user", "key": "script_key"}
        # Test endpoint
        responses.add(responses.POST, HOST + "/api/v2/shotgun/config/test/", json={"ok": True}, status=200)
        # Config endpoint
        responses.add(responses.POST, HOST + "/api/v2/shotgun/config/", json={"id": 1}, status=200)

        result = api.shotgrid_create_config(1, syncsketch_project_id=10, data=data)
        assert hasattr(result, "status_code")  # raw_response=True default
        assert result.status_code == 200

    @responses.activate
    def test_test_fails_raises(self, api):
        data = {"url": "https://sg.example.com", "username": "user", "key": "key"}
        responses.add(responses.POST, HOST + "/api/v2/shotgun/config/test/", json={}, status=400)

        with pytest.raises(Exception, match="configuration test failed"):
            api.shotgrid_create_config(1, data=data)

    def test_missing_url_asserts(self, api):
        with pytest.raises(AssertionError):
            api.shotgrid_create_config(1, data={"username": "u", "key": "k"})

    def test_missing_username_asserts(self, api):
        with pytest.raises(AssertionError):
            api.shotgrid_create_config(1, data={"url": "http://sg", "key": "k"})

    def test_missing_key_asserts(self, api):
        with pytest.raises(AssertionError):
            api.shotgrid_create_config(1, data={"url": "http://sg", "username": "u"})

    def test_non_dict_asserts(self, api):
        with pytest.raises(AssertionError):
            api.shotgrid_create_config(1, data="not a dict")


class TestShotgridGetPlaylists:
    @responses.activate
    def test_get_playlists(self, api):
        responses.add(responses.GET, HOST + "/api/v2/shotgun/playlists/1/10/", json={"playlists": []})
        result = api.shotgrid_get_playlists(1, 10)
        assert "playlists" in result

    @responses.activate
    def test_with_shotgun_project_id(self, api):
        responses.add(responses.GET, HOST + "/api/v2/shotgun/playlists/1/10/", json={})
        api.shotgrid_get_playlists(1, 10, shotgun_project_id=99)
        assert responses.calls[0].request.params["shotgun_project_id"] == "99"


class TestShotgridSyncReviewNotes:
    @responses.activate
    def test_sync_notes(self, api):
        url = HOST + "/api/v2/shotgun/sync-review-notes/review/456/"
        responses.add(responses.POST, url, json={"status": "processing", "task_id": "t1"})
        result = api.shotgrid_sync_review_notes(456)
        assert result["task_id"] == "t1"


class TestShotgridSyncNewItemNotes:
    @responses.activate
    def test_sync_item_notes(self, api):
        url = HOST + "/api/v2/shotgun/sync-notes/project/123/review/456/789/"
        responses.add(responses.POST, url, json={"comments": 3, "sketches": 1})
        result = api.shotgrid_sync_new_item_notes(123, 456, 789)
        assert result["comments"] == 3


class TestGetShotgridSyncReviewNotesProgress:
    @responses.activate
    def test_get_progress(self, api):
        url = HOST + "/api/v2/shotgun/sync-review-notes/task-1/"
        responses.add(responses.GET, url, json={"status": "done", "percent_complete": 100})
        result = api.get_shotgrid_sync_review_notes_progress("task-1")
        assert result["percent_complete"] == 100


class TestShotgridSyncReviewItems:
    @responses.activate
    def test_sync_items(self, api):
        check_url = HOST + "/api/v2/shotgun/sync-items/project/123/check/"
        responses.add(
            responses.POST,
            check_url,
            json={
                "review_id": 456,
                "items": [{"id": 1, "name": "shot1"}, {"id": 2, "name": "shot2"}],
            },
        )
        # Per-item sync calls
        sync_url = HOST + "/api/v2/shotgun/sync-items/project/123/review/456/"
        responses.add(responses.POST, sync_url, json={"id": 101})
        responses.add(responses.POST, sync_url, json={"id": 102})

        result = api.shotgrid_sync_review_items(123, "playlist_code", 999)
        assert result["review_id"] == 456
        assert result["items"] == [101, 102]
        assert result["total_items"] == 2
        assert result["status"] == "done"

    @responses.activate
    def test_with_review_id(self, api):
        check_url = HOST + "/api/v2/shotgun/sync-items/project/123/review/456/check/"
        responses.add(responses.POST, check_url, json={"review_id": 456, "items": []})
        result = api.shotgrid_sync_review_items(123, "code", 999, review_id=456)
        assert result["review_id"] == 456


class TestShotgridGetProjects:
    def test_raises_deprecation(self, api):
        with pytest.raises(DeprecationWarning):
            api.shotgrid_get_projects(123)


class TestGetShotgridSyncReviewItemsProgress:
    def test_raises_deprecation(self, api):
        with pytest.raises(DeprecationWarning):
            api.get_shotgrid_sync_review_items_progress("task-1")
