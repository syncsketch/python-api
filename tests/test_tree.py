"""Tests for get_tree method."""

import responses

from tests.conftest import HOST


class TestGetTree:
    @responses.activate
    def test_without_items(self, api):
        tree_data = {"accounts": [{"id": 1, "projects": []}]}
        responses.add(responses.GET, HOST + "/api/v1/person/tree/", json=tree_data)
        result = api.get_tree()
        assert result == tree_data
        assert "fetchItems" not in responses.calls[0].request.params

    @responses.activate
    def test_with_items(self, api):
        responses.add(responses.GET, HOST + "/api/v1/person/tree/", json={})
        api.get_tree(withItems=True)
        assert responses.calls[0].request.params["fetchItems"] == "1"

    @responses.activate
    def test_raw_response(self, api):
        responses.add(responses.GET, HOST + "/api/v1/person/tree/", json={})
        result = api.get_tree(raw_response=True)
        assert hasattr(result, "status_code")
