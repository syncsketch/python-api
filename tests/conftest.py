import pytest
import responses

from syncsketch import SyncSketchAPI

HOST = "https://test.syncsketch.com"
USERNAME = "testuser"
API_KEY = "testapikey123"


@pytest.fixture
def api():
    """Standard API client using default query-param auth."""
    return SyncSketchAPI(
        auth=USERNAME,
        api_key=API_KEY,
        host=HOST,
    )


@pytest.fixture
def api_token():
    """API client using expiring token auth."""
    return SyncSketchAPI(
        auth="test@example.com",
        api_key="expiring-token-123",
        host=HOST,
        useExpiringToken=True,
    )


@pytest.fixture
def api_header():
    """API client using header-based auth."""
    return SyncSketchAPI(
        auth=USERNAME,
        api_key=API_KEY,
        host=HOST,
        use_header_auth=True,
    )


@pytest.fixture
def api_debug():
    """API client with debug enabled."""
    return SyncSketchAPI(
        auth=USERNAME,
        api_key=API_KEY,
        host=HOST,
        debug=True,
    )


@pytest.fixture
def mocked():
    """Activate the responses mock for the duration of a test."""
    with responses.RequestsMock() as rsps:
        yield rsps


def make_list_response(objects, total_count=None):
    """Build a standard Tastypie list response envelope."""
    if total_count is None:
        total_count = len(objects)
    return {
        "meta": {
            "limit": 100,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": total_count,
        },
        "objects": objects,
    }


SAMPLE_PROJECT = {
    "id": 123,
    "name": "Test Project",
    "description": "A test project",
    "active": True,
    "is_archived": False,
    "account_id": 1,
}

SAMPLE_REVIEW = {
    "id": 456,
    "name": "Test Review",
    "description": "A test review",
    "active": True,
    "project": "/api/v1/project/123/",
    "uuid": "abc-def-ghi",
}

SAMPLE_ITEM = {
    "id": 789,
    "name": "test_clip.mp4",
    "active": True,
    "fps": 24.0,
    "status": "done",
    "revision_id": 101,
}

SAMPLE_USER = {
    "id": 42,
    "first_name": "Test",
    "last_name": "User",
    "email": "test@example.com",
}
