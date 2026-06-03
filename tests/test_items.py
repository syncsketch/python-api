"""Tests for item CRUD methods (excluding uploads)."""

import json

import responses

from tests.conftest import HOST, SAMPLE_ITEM, make_list_response


class TestGetItem:
    @responses.activate
    def test_get_item(self, api):
        responses.add(responses.GET, HOST + "/api/v1/item/789/", json=SAMPLE_ITEM)
        result = api.get_item(789)
        assert result["id"] == 789

    @responses.activate
    def test_get_item_with_data_and_fields(self, api):
        responses.add(responses.GET, HOST + "/api/v1/item/789/", json=SAMPLE_ITEM)
        api.get_item(789, data={"review_id": 456}, fields=["id", "name"])
        params = responses.calls[0].request.params
        assert params["review_id"] == "456"
        assert params["fields"] == "id,name"


class TestUpdateItem:
    @responses.activate
    def test_update_item(self, api):
        responses.add(responses.PATCH, HOST + "/api/v1/item/789/", json={"id": 789, "name": "Updated"})
        result = api.update_item(789, {"name": "Updated"})
        assert result["name"] == "Updated"

    def test_non_dict_returns_false(self, api):
        assert api.update_item(789, "not a dict") is False


class TestAddItem:
    @responses.activate
    def test_add_item(self, api):
        responses.add(responses.POST, HOST + "/api/v1/item/", json=SAMPLE_ITEM)
        additional_data = {"external_url": "https://example.com/video.mp4"}
        result = api.add_item(456, "test_clip.mp4", 24.0, additional_data)
        assert result["id"] == 789
        body = json.loads(responses.calls[0].request.body)
        assert body["reviewId"] == 456
        assert body["name"] == "test_clip.mp4"
        assert body["fps"] == 24.0
        assert body["status"] == "done"
        assert body["external_url"] == "https://example.com/video.mp4"


class TestGetMedia:
    @responses.activate
    def test_get_media(self, api):
        responses.add(responses.GET, HOST + "/api/v1/item/", json=make_list_response([SAMPLE_ITEM]))
        result = api.get_media({"reviews__project__name": "test", "limit": 1, "active": 1})
        assert len(result["objects"]) == 1


class TestGetItemsByReviewId:
    @responses.activate
    def test_get_items_by_review_id(self, api):
        responses.add(responses.GET, HOST + "/api/v1/item/", json=make_list_response([SAMPLE_ITEM]))
        api.get_items_by_review_id(456)
        params = responses.calls[0].request.params
        assert params["reviews__id"] == "456"
        assert params["active"] == "1"


class TestDeleteItem:
    @responses.activate
    def test_delete_item(self, api):
        responses.add(responses.PATCH, HOST + "/api/v1/item/789/", json={})
        api.delete_item(789)
        body = json.loads(responses.calls[0].request.body)
        assert body["active"] is False


class TestBulkDeleteItems:
    @responses.activate
    def test_bulk_delete_items(self, api):
        responses.add(responses.POST, HOST + "/api/v2/bulk-delete-items/", json={}, status=200)
        result = api.bulk_delete_items([1, 2, 3])
        # Default raw_response=True
        assert hasattr(result, "status_code")
        body = json.loads(responses.calls[0].request.body)
        assert body["item_ids"] == [1, 2, 3]


class TestConnectItemToReview:
    def test_deprecated(self, api):
        result = api.connect_item_to_review(789, 456)
        assert result == "Deprecated"


class TestMoveItems:
    @responses.activate
    def test_move_items(self, api):
        item_data = [{"review_id": 1, "item_id": 1}, {"review_id": 1, "item_id": 2}]
        responses.add(responses.POST, HOST + "/api/v2/move-review-items/", json={}, status=200)
        result = api.move_items(999, item_data)
        # Default raw_response=True
        assert hasattr(result, "status_code")
        body = json.loads(responses.calls[0].request.body)
        assert body["new_review_id"] == 999
        assert body["item_data"] == item_data
