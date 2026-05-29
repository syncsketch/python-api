"""Tests for user lookup and access control methods."""

import json

import responses

from tests.conftest import HOST, SAMPLE_USER, make_list_response


class TestGetUsersByName:
    @responses.activate
    def test_search_by_name(self, api):
        responses.add(responses.GET, HOST + "/api/v1/simpleperson/", json=make_list_response([SAMPLE_USER]))
        api.get_users_by_name("Test")
        assert responses.calls[0].request.params["name"] == "Test"


class TestGetUserByEmail:
    @responses.activate
    def test_found(self, api):
        responses.add(
            responses.GET,
            HOST + "/api/v1/simpleperson/",
            json=make_list_response([SAMPLE_USER]),
        )
        result = api.get_user_by_email("test@example.com")
        assert result["email"] == "test@example.com"
        assert responses.calls[0].request.params["email__iexact"] == "test@example.com"

    @responses.activate
    def test_not_found(self, api):
        responses.add(
            responses.GET,
            HOST + "/api/v1/simpleperson/",
            json=make_list_response([]),
        )
        result = api.get_user_by_email("nobody@example.com")
        assert result is None


class TestGetUsersByProjectId:
    @responses.activate
    def test_get_users(self, api):
        responses.add(responses.GET, HOST + "/api/v2/all-project-users/123/", json=[SAMPLE_USER])
        result = api.get_users_by_project_id(123)
        assert result[0]["id"] == 42


class TestGetConnectionsByUserId:
    @responses.activate
    def test_basic(self, api):
        responses.add(responses.GET, HOST + "/api/v2/user/42/connections/account/1/", json=[])
        api.get_connections_by_user_id(42, 1)
        assert "/api/v2/user/42/connections/account/1/" in responses.calls[0].request.url

    @responses.activate
    def test_with_flags(self, api):
        responses.add(responses.GET, HOST + "/api/v2/user/42/connections/account/1/", json=[])
        api.get_connections_by_user_id(42, 1, include_inactive=True, include_archived=False)
        params = responses.calls[0].request.params
        assert params["include_inactive"] == "true"
        assert params["include_archived"] == "false"


class TestGetUserById:
    @responses.activate
    def test_get_by_id(self, api):
        responses.add(responses.GET, HOST + "/api/v1/simpleperson/42/", json=SAMPLE_USER)
        result = api.get_user_by_id(42)
        assert result["id"] == 42


class TestGetCurrentUser:
    @responses.activate
    def test_get_current_user(self, api):
        responses.add(responses.GET, HOST + "/api/v1/simpleperson/currentUser/", json=SAMPLE_USER)
        result = api.get_current_user()
        assert result["email"] == "test@example.com"


class TestAddUsersToWorkspace:
    @responses.activate
    def test_add_users(self, api):
        users = [{"email": "new@test.de", "permission": "admin"}]
        responses.add(responses.POST, HOST + "/api/v2/add-users/", json={"success": True})
        api.add_users_to_workspace(1, users, note="Welcome!")
        body = json.loads(responses.calls[0].request.body)
        assert body["which"] == "account"
        assert body["entity_id"] == 1
        assert body["note"] == "Welcome!"
        assert json.loads(body["users"]) == users

    def test_non_list_returns_false(self, api):
        assert api.add_users_to_workspace(1, "not a list") is False


class TestRemoveUsersFromWorkspace:
    @responses.activate
    def test_remove_users(self, api):
        users = [{"email": "old@test.de"}]
        responses.add(responses.POST, HOST + "/api/v2/remove-users/", json={"success": True})
        api.remove_users_from_workspace(1, users)
        body = json.loads(responses.calls[0].request.body)
        assert body["which"] == "account"
        assert body["entity_id"] == 1

    def test_non_list_returns_false(self, api):
        assert api.remove_users_from_workspace(1, "not a list") is False


class TestAddUsersToProject:
    @responses.activate
    def test_add_users(self, api):
        users = [{"email": "new@test.de", "permission": "viewer"}]
        responses.add(responses.POST, HOST + "/api/v2/add-users/", json={"success": True})
        api.add_users_to_project(123, users, note="Invite")
        body = json.loads(responses.calls[0].request.body)
        assert body["which"] == "project"
        assert body["entity_id"] == 123

    def test_non_list_returns_false(self, api):
        assert api.add_users_to_project(123, "not a list") is False


class TestRemoveUsersFromProject:
    @responses.activate
    def test_remove_users(self, api):
        users = [{"email": "old@test.de"}]
        responses.add(responses.POST, HOST + "/api/v2/remove-users/", json={"success": True})
        api.remove_users_from_project(123, users)
        body = json.loads(responses.calls[0].request.body)
        assert body["which"] == "project"
        assert body["entity_id"] == 123

    def test_non_list_returns_false(self, api):
        assert api.remove_users_from_project(123, "not a list") is False


class TestAddUsersDeprecated:
    @responses.activate
    def test_delegates_to_add_users_to_project(self, api):
        users = [{"email": "test@test.de", "permission": "viewer"}]
        responses.add(responses.POST, HOST + "/api/v2/add-users/", json={"success": True})
        api.add_users(123, users)
        body = json.loads(responses.calls[0].request.body)
        assert body["which"] == "project"
