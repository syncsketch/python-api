"""Tests for review CRUD and section methods."""

import json

import responses

from tests.conftest import HOST, SAMPLE_REVIEW, make_list_response


class TestCreateReview:
    @responses.activate
    def test_create_review(self, api):
        responses.add(responses.POST, HOST + "/api/v1/review/", json=SAMPLE_REVIEW)
        result = api.create_review(123, "Test Review", "A test review")
        assert result["id"] == 456
        body = json.loads(responses.calls[0].request.body)
        assert body["project"] == "/api/v1/project/123/"
        assert body["name"] == "Test Review"
        assert body["description"] == "A test review"

    @responses.activate
    def test_create_review_with_extra_data(self, api):
        responses.add(responses.POST, HOST + "/api/v1/review/", json=SAMPLE_REVIEW)
        api.create_review(123, "Test", data={"deadline": "2026-01-01"})
        body = json.loads(responses.calls[0].request.body)
        assert body["deadline"] == "2026-01-01"


class TestGetReviews:
    @responses.activate
    def test_get_reviews_by_project_id(self, api):
        responses.add(responses.GET, HOST + "/api/v1/review/", json=make_list_response([SAMPLE_REVIEW]))
        api.get_reviews_by_project_id(123)
        params = responses.calls[0].request.params
        assert params["project__id"] == "123"
        assert params["project__active"] == "1"
        assert params["project__is_archived"] == "0"

    @responses.activate
    def test_get_reviews_with_pagination(self, api):
        responses.add(responses.GET, HOST + "/api/v1/review/", json=make_list_response([]))
        api.get_reviews_by_project_id(123, limit=50, offset=10)
        params = responses.calls[0].request.params
        assert params["limit"] == "50"
        assert params["offset"] == "10"

    @responses.activate
    def test_get_review_by_name(self, api):
        responses.add(responses.GET, HOST + "/api/v1/review/", json=make_list_response([SAMPLE_REVIEW]))
        api.get_review_by_name("Test")
        params = responses.calls[0].request.params
        assert params["name__istartswith"] == "Test"
        assert params["active"] == "True"

    @responses.activate
    def test_get_review_by_id(self, api):
        responses.add(responses.GET, HOST + "/api/v1/review/456/", json=SAMPLE_REVIEW)
        result = api.get_review_by_id(456)
        assert result["id"] == 456


class TestGetReviewByUuid:
    @responses.activate
    def test_found(self, api):
        responses.add(
            responses.GET,
            HOST + "/api/v1/review/",
            json=make_list_response([SAMPLE_REVIEW]),
        )
        result = api.get_review_by_uuid("abc-def-ghi")
        assert result["uuid"] == "abc-def-ghi"

    @responses.activate
    def test_not_found(self, api):
        responses.add(responses.GET, HOST + "/api/v1/review/", json=make_list_response([]))
        result = api.get_review_by_uuid("nonexistent")
        assert result is None

    @responses.activate
    def test_raw_response(self, api):
        responses.add(responses.GET, HOST + "/api/v1/review/", json=make_list_response([SAMPLE_REVIEW]))
        result = api.get_review_by_uuid("abc-def-ghi", raw_response=True)
        assert hasattr(result, "status_code")


class TestReviewStorage:
    @responses.activate
    def test_get_review_storage(self, api):
        responses.add(responses.GET, HOST + "/api/v2/review/456/storage/", json={"storage": 5000})
        result = api.get_review_storage(456)
        assert result["storage"] == 5000


class TestUpdateReview:
    @responses.activate
    def test_update_review(self, api):
        responses.add(responses.PATCH, HOST + "/api/v1/review/456/", json={"id": 456, "name": "Updated"})
        result = api.update_review(456, {"name": "Updated"})
        assert result["name"] == "Updated"

    def test_non_dict_returns_false(self, api):
        assert api.update_review(456, "not a dict") is False


class TestSortReviewItems:
    @responses.activate
    def test_sort_items(self, api):
        items = [{"id": 1, "sortorder": 0}, {"id": 2, "sortorder": 1}]
        responses.add(responses.PUT, HOST + "/api/v2/review/456/sort_items/", json={"updated_items": 2})
        result = api.sort_review_items(456, items)
        assert result["updated_items"] == 2

    def test_non_list_returns_false(self, api):
        assert api.sort_review_items(456, "not a list") is False


class TestArchiveRestoreDeleteReview:
    @responses.activate
    def test_archive_review(self, api):
        responses.add(responses.POST, HOST + "/api/v2/review/456/archive/", json={}, status=200)
        result = api.archive_review(456)
        # Default raw_response=True
        assert hasattr(result, "status_code")

    @responses.activate
    def test_restore_review(self, api):
        responses.add(responses.POST, HOST + "/api/v2/review/456/restore/", json={}, status=200)
        result = api.restore_review(456)
        assert hasattr(result, "status_code")

    @responses.activate
    def test_delete_review(self, api):
        responses.add(responses.PATCH, HOST + "/api/v1/review/456/", json={})
        api.delete_review(456)
        body = json.loads(responses.calls[0].request.body)
        assert body["active"] is False


class TestReviewSections:
    @responses.activate
    def test_create_section(self, api):
        responses.add(responses.POST, HOST + "/api/v2/review/456/sections/create/", json={"name": "Section 1"})
        result = api.create_review_section(456, "Section 1", [1, 2, 3])
        body = json.loads(responses.calls[0].request.body)
        assert body["name"] == "Section 1"
        assert body["itemIds"] == [1, 2, 3]
        assert "uuid" not in body

    @responses.activate
    def test_create_section_with_uuid(self, api):
        responses.add(responses.POST, HOST + "/api/v2/review/456/sections/create/", json={})
        api.create_review_section(456, "Section", [1], uuid="my-uuid")
        body = json.loads(responses.calls[0].request.body)
        assert body["uuid"] == "my-uuid"

    @responses.activate
    def test_update_sections(self, api):
        data = [{"uuid": "sec-1", "name": "Updated", "itemIds": [1, 2]}]
        responses.add(responses.PUT, HOST + "/api/v2/review/456/sections/bulk-update/", json={})
        api.update_review_sections(456, data)
        assert responses.calls[0].request.method == "PUT"

    @responses.activate
    def test_delete_section(self, api):
        responses.add(responses.DELETE, HOST + "/api/v2/review/456/sections/sec-uuid-1/", json={})
        api.delete_review_section(456, "sec-uuid-1")
        assert responses.calls[0].request.method == "DELETE"
