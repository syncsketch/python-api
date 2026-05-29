"""Tests for SyncSketchAPI constructor and authentication modes."""

from syncsketch import SyncSketchAPI

HOST = "https://test.syncsketch.com"


class TestDefaultAuth:
    def test_query_params_set(self, api):
        assert api.api_params == {"api_key": "testapikey123", "username": "testuser"}

    def test_headers_empty(self, api):
        assert api.headers == {}


class TestExpiringTokenAuth:
    def test_token_params_set(self, api_token):
        assert api_token.api_params == {
            "token": "expiring-token-123",
            "email": "test@example.com",
        }

    def test_headers_empty(self, api_token):
        assert api_token.headers == {}


class TestHeaderAuth:
    def test_authorization_header_set(self, api_header):
        assert api_header.headers == {
            "Authorization": "apikey testuser:testapikey123",
        }

    def test_api_params_empty(self, api_header):
        assert api_header.api_params == {}

    def test_header_auth_with_expiring_token(self):
        api = SyncSketchAPI(
            auth="test@example.com",
            api_key="expiring-token-123",
            host=HOST,
            useExpiringToken=True,
            use_header_auth=True,
        )
        assert api.headers["Authorization"] == "token test@example.com:expiring-token-123"
        assert api.api_params == {}


class TestConstructorOptions:
    def test_host_trailing_slash_stripped(self):
        api = SyncSketchAPI(auth="u", api_key="k", host="https://test.syncsketch.com/")
        assert api.HOST == "https://test.syncsketch.com"

    def test_default_api_version(self, api):
        assert api.api_version == "v1"

    def test_custom_api_version(self):
        api = SyncSketchAPI(auth="u", api_key="k", host=HOST, api_version="v2")
        assert api.api_version == "v2"

    def test_debug_default_false(self, api):
        assert api.debug is False

    def test_debug_true(self, api_debug):
        assert api_debug.debug is True
