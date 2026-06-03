"""Tests for project CRUD methods."""

import json

import responses

from tests.conftest import HOST, SAMPLE_PROJECT, make_list_response


class TestCreateProject:
    @responses.activate
    def test_create_project(self, api):
        responses.add(responses.POST, HOST + "/api/v1/project/", json=SAMPLE_PROJECT)
        result = api.create_project(1, "Test Project", "A test project")
        assert result["id"] == 123
        body = json.loads(responses.calls[0].request.body)
        assert body["name"] == "Test Project"
        assert body["description"] == "A test project"
        assert body["account_id"] == 1

    @responses.activate
    def test_create_project_with_extra_data(self, api):
        responses.add(responses.POST, HOST + "/api/v1/project/", json=SAMPLE_PROJECT)
        api.create_project(1, "Test", data={"is_public": True})
        body = json.loads(responses.calls[0].request.body)
        assert body["is_public"] is True


class TestGetProjects:
    @responses.activate
    def test_default_params(self, api):
        responses.add(responses.GET, HOST + "/api/v1/project/", json=make_list_response([SAMPLE_PROJECT]))
        api.get_projects()
        params = responses.calls[0].request.params
        assert params["active"] == "1"
        assert params["is_archived"] == "0"
        assert params["account__active"] == "1"
        assert params["limit"] == "100"
        assert params["offset"] == "0"

    @responses.activate
    def test_include_deleted(self, api):
        responses.add(responses.GET, HOST + "/api/v1/project/", json=make_list_response([]))
        api.get_projects(include_deleted=True)
        params = responses.calls[0].request.params
        assert "active" not in params

    @responses.activate
    def test_include_archived(self, api):
        responses.add(responses.GET, HOST + "/api/v1/project/", json=make_list_response([]))
        api.get_projects(include_archived=True)
        params = responses.calls[0].request.params
        assert "active" not in params
        assert "is_archived" not in params

    @responses.activate
    def test_include_tags(self, api):
        responses.add(responses.GET, HOST + "/api/v1/project/", json=make_list_response([]))
        api.get_projects(include_tags=True)
        assert responses.calls[0].request.params["include_tags"] == "1"

    @responses.activate
    def test_include_connections(self, api):
        responses.add(responses.GET, HOST + "/api/v1/project/", json=make_list_response([]))
        api.get_projects(include_connections=True)
        assert responses.calls[0].request.params["withFullConnections"] == "True"

    @responses.activate
    def test_custom_limit_offset(self, api):
        responses.add(responses.GET, HOST + "/api/v1/project/", json=make_list_response([]))
        api.get_projects(limit=50, offset=10)
        params = responses.calls[0].request.params
        assert params["limit"] == "50"
        assert params["offset"] == "10"

    @responses.activate
    def test_with_fields(self, api):
        responses.add(responses.GET, HOST + "/api/v1/project/", json=make_list_response([]))
        api.get_projects(fields=["id", "name"])
        assert responses.calls[0].request.params["fields"] == "id,name"


class TestGetProjectsByName:
    @responses.activate
    def test_search_by_name(self, api):
        responses.add(responses.GET, HOST + "/api/v1/project/", json=make_list_response([SAMPLE_PROJECT]))
        api.get_projects_by_name("Test")
        assert responses.calls[0].request.params["name__istartswith"] == "Test"


class TestGetProjectById:
    @responses.activate
    def test_get_by_id(self, api):
        responses.add(responses.GET, HOST + "/api/v1/project/123/", json=SAMPLE_PROJECT)
        result = api.get_project_by_id(123)
        assert result["id"] == 123


class TestGetProjectStorage:
    @responses.activate
    def test_get_storage(self, api):
        responses.add(responses.GET, HOST + "/api/v2/project/123/storage/", json={"storage": 12345})
        result = api.get_project_storage(123)
        assert result["storage"] == 12345


class TestUpdateProject:
    @responses.activate
    def test_update_project(self, api):
        responses.add(responses.PATCH, HOST + "/api/v1/project/123/", json={"id": 123, "name": "Updated"})
        result = api.update_project(123, {"name": "Updated"})
        assert result["name"] == "Updated"

    def test_non_dict_returns_false(self, api):
        assert api.update_project(123, "not a dict") is False


class TestDeleteProject:
    @responses.activate
    def test_delete_project(self, api):
        responses.add(responses.PATCH, HOST + "/api/v1/project/123/", json={})
        api.delete_project(123)
        body = json.loads(responses.calls[0].request.body)
        assert body["active"] is False


class TestDuplicateProject:
    @responses.activate
    def test_duplicate_project(self, api):
        responses.add(responses.POST, HOST + "/api/v2/project/123/duplicate/", json={"id": 999})
        result = api.duplicate_project(123, copy_reviews=True, copy_users=True)
        assert result["id"] == 999
        body = json.loads(responses.calls[0].request.body)
        assert body["reviews"] is True
        assert body["users"] is True

    @responses.activate
    def test_duplicate_with_name(self, api):
        responses.add(responses.POST, HOST + "/api/v2/project/123/duplicate/", json={"id": 999})
        api.duplicate_project(123, name="Copy of Project")
        body = json.loads(responses.calls[0].request.body)
        assert body["name"] == "Copy of Project"


class TestArchiveRestoreProject:
    @responses.activate
    def test_archive_project(self, api):
        responses.add(responses.PATCH, HOST + "/api/v1/project/123/", json={})
        api.archive_project(123)
        body = json.loads(responses.calls[0].request.body)
        assert body["is_archived"] is True

    @responses.activate
    def test_restore_project(self, api):
        responses.add(responses.PATCH, HOST + "/api/v1/project/123/", json={})
        api.restore_project(123)
        body = json.loads(responses.calls[0].request.body)
        assert body["is_archived"] is False
