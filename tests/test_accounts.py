"""Tests for workspace/account methods."""

import responses

from tests.conftest import HOST, SAMPLE_PROJECT, make_list_response


class TestGetAccounts:
    @responses.activate
    def test_get_accounts(self, api):
        body = make_list_response([{"id": 1, "name": "Workspace"}])
        responses.add(responses.GET, HOST + "/api/v1/account/", json=body)
        result = api.get_accounts()
        assert result["objects"][0]["name"] == "Workspace"
        assert responses.calls[0].request.params["active"] == "1"

    @responses.activate
    def test_get_accounts_with_fields(self, api):
        responses.add(responses.GET, HOST + "/api/v1/account/", json=make_list_response([]))
        api.get_accounts(fields=["id", "name"])
        assert responses.calls[0].request.params["fields"] == "id,name"

    @responses.activate
    def test_get_accounts_raw_response(self, api):
        responses.add(responses.GET, HOST + "/api/v1/account/", json={})
        result = api.get_accounts(raw_response=True)
        assert hasattr(result, "status_code")


class TestUpdateAccount:
    @responses.activate
    def test_update_account(self, api):
        responses.add(responses.PATCH, HOST + "/api/v1/account/1/", json={"id": 1, "name": "Updated"})
        result = api.update_account(1, {"name": "Updated"})
        assert result["name"] == "Updated"

    def test_update_account_non_dict_returns_false(self, api):
        result = api.update_account(1, "not a dict")
        assert result is False
