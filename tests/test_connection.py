"""Tests for connection, URL utilities, and _update_params."""

import responses

from syncsketch import SyncSketchAPI

HOST = "https://test.syncsketch.com"


class TestIsConnected:
    @responses.activate
    def test_raw_response_returns_response_object(self, api):
        responses.add(responses.GET, HOST + "/api/v1/person/connected/", json={}, status=200)
        result = api.is_connected(raw_response=True)
        assert hasattr(result, "status_code")
        assert result.status_code == 200


class TestGetApiBaseUrl:
    def test_default_version(self, api):
        assert api.get_api_base_url() == HOST + "/api/v1/"

    def test_custom_version(self, api):
        assert api.get_api_base_url("v2") == HOST + "/api/v2/"


class TestJoinUrlPath:
    def test_single_segment(self):
        assert SyncSketchAPI.join_url_path("abc") == "abc/"

    def test_two_segments(self):
        assert SyncSketchAPI.join_url_path("abc", "123") == "abc/123/"

    def test_strips_slashes(self):
        assert SyncSketchAPI.join_url_path("abc", "/123/", "/xyz/") == "abc/123/xyz/"

    def test_already_terminated(self):
        assert SyncSketchAPI.join_url_path("abc/") == "abc/"


class TestUpdateParams:
    def test_string_value(self):
        params = {}
        SyncSketchAPI._update_params("key", "val", params)
        assert params == {"key": "val"}

    def test_list_value_joined(self):
        params = {}
        SyncSketchAPI._update_params("key", ["a", "b", "c"], params)
        assert params == {"key": "a,b,c"}

    def test_tuple_value_joined(self):
        params = {}
        SyncSketchAPI._update_params("key", ("x", "y"), params)
        assert params == {"key": "x,y"}

    def test_none_does_not_update(self):
        params = {"existing": 1}
        SyncSketchAPI._update_params("key", None, params)
        assert params == {"existing": 1}

    def test_falsy_zero_does_not_update(self):
        params = {}
        SyncSketchAPI._update_params("key", 0, params)
        assert params == {}
