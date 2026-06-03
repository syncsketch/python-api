"""Tests for _get_json_response HTTP dispatch logic."""

import json

import responses

HOST = "https://test.syncsketch.com"


class TestHTTPMethodRouting:
    @responses.activate
    def test_get_request_default(self, api):
        responses.add(responses.GET, HOST + "/api/v1/test/", json={"ok": True})
        result = api._get_json_response("/api/v1/test/")
        assert result == {"ok": True}
        assert responses.calls[0].request.method == "GET"

    @responses.activate
    def test_post_request_with_post_data(self, api):
        responses.add(responses.POST, HOST + "/api/v1/test/", json={"created": True})
        result = api._get_json_response("/api/v1/test/", postData={"key": "val"})
        assert result == {"created": True}
        req = responses.calls[0].request
        assert req.method == "POST"
        assert json.loads(req.body) == {"key": "val"}

    @responses.activate
    def test_patch_request_with_patch_data(self, api):
        responses.add(responses.PATCH, HOST + "/api/v1/test/", json={"updated": True})
        result = api._get_json_response("/api/v1/test/", patchData={"key": "val"})
        assert result == {"updated": True}
        assert responses.calls[0].request.method == "PATCH"

    @responses.activate
    def test_put_request_with_put_data(self, api):
        responses.add(responses.PUT, HOST + "/api/v1/test/", json={"updated": True})
        result = api._get_json_response("/api/v1/test/", putData={"key": "val"})
        assert result == {"updated": True}
        assert responses.calls[0].request.method == "PUT"

    @responses.activate
    def test_delete_request(self, api):
        responses.add(responses.DELETE, HOST + "/api/v1/test/", json={"deleted": True})
        result = api._get_json_response("/api/v1/test/", method="delete")
        assert result == {"deleted": True}
        assert responses.calls[0].request.method == "DELETE"

    @responses.activate
    def test_explicit_post_method_no_data(self, api):
        responses.add(responses.POST, HOST + "/api/v1/test/", json={"ok": True})
        api._get_json_response("/api/v1/test/", method="post")
        assert responses.calls[0].request.method == "POST"


class TestAuthParamInjection:
    @responses.activate
    def test_get_data_merged_with_auth_params(self, api):
        responses.add(responses.GET, HOST + "/api/v1/test/", json={})
        api._get_json_response("/api/v1/test/", getData={"limit": 10})
        params = responses.calls[0].request.params
        assert params["api_key"] == "testapikey123"
        assert params["username"] == "testuser"
        assert params["limit"] == "10"

    @responses.activate
    def test_header_auth_sends_authorization_header(self, api_header):
        responses.add(responses.GET, HOST + "/api/v1/test/", json={})
        api_header._get_json_response("/api/v1/test/")
        headers = responses.calls[0].request.headers
        assert "Authorization" in headers
        assert headers["Authorization"] == "apikey testuser:testapikey123"
        # No auth query params
        params = responses.calls[0].request.params
        assert "api_key" not in params
        assert "username" not in params

    @responses.activate
    def test_token_auth_sends_token_params(self, api_token):
        responses.add(responses.GET, HOST + "/api/v1/test/", json={})
        api_token._get_json_response("/api/v1/test/")
        params = responses.calls[0].request.params
        assert params["token"] == "expiring-token-123"
        assert params["email"] == "test@example.com"


class TestContentType:
    @responses.activate
    def test_default_content_type(self, api):
        responses.add(responses.GET, HOST + "/api/v1/test/", json={})
        api._get_json_response("/api/v1/test/")
        assert responses.calls[0].request.headers["Content-Type"] == "application/json"

    @responses.activate
    def test_custom_content_type(self, api):
        responses.add(responses.GET, HOST + "/api/v1/test/", json={})
        api._get_json_response("/api/v1/test/", content_type="text/plain")
        assert responses.calls[0].request.headers["Content-Type"] == "text/plain"


class TestResponseHandling:
    @responses.activate
    def test_raw_response_returns_response_object(self, api):
        responses.add(responses.GET, HOST + "/api/v1/test/", json={"ok": True})
        result = api._get_json_response("/api/v1/test/", raw_response=True)
        assert hasattr(result, "status_code")
        assert result.status_code == 200
        assert result.json() == {"ok": True}

    @responses.activate
    def test_json_parse_success(self, api):
        responses.add(responses.GET, HOST + "/api/v1/test/", json={"data": [1, 2, 3]})
        result = api._get_json_response("/api/v1/test/")
        assert result == {"data": [1, 2, 3]}

    @responses.activate
    def test_json_parse_failure_returns_empty_objects(self, api):
        responses.add(responses.GET, HOST + "/api/v1/test/", body="not json", status=200)
        result = api._get_json_response("/api/v1/test/")
        assert result == {"objects": []}


class TestURLHandling:
    @responses.activate
    def test_full_url_passthrough(self, api):
        responses.add(responses.GET, "https://other.example.com/api/test/", json={})
        api._get_json_response("https://other.example.com/api/test/")
        assert "other.example.com" in responses.calls[0].request.url

    @responses.activate
    def test_relative_url_gets_host_prefix(self, api):
        responses.add(responses.GET, HOST + "/api/v1/project/", json={})
        api._get_json_response("/api/v1/project/")
        assert responses.calls[0].request.url.startswith(HOST)
