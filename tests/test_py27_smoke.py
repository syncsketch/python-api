"""
Minimal smoke test for Python 2.7 compatibility.

Run directly: python2.7 tests/test_py27_smoke.py

This verifies that the module imports and core construction works
under Python 2.7 without requiring pytest or other test dependencies.
"""

import sys
import os

# Ensure the package root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from syncsketch import SyncSketchAPI


def test_default_auth():
    api = SyncSketchAPI("testuser", "testapikey")
    assert api.api_params == {"api_key": "testapikey", "username": "testuser"}
    assert api.headers == {}
    assert api.HOST == "https://www.syncsketch.com"
    assert api.api_version == "v1"


def test_expiring_token_auth():
    api = SyncSketchAPI("test@example.com", "token123", useExpiringToken=True)
    assert api.api_params == {"token": "token123", "email": "test@example.com"}


def test_header_auth():
    api = SyncSketchAPI("testuser", "testapikey", use_header_auth=True)
    assert api.headers == {"Authorization": "apikey testuser:testapikey"}
    assert api.api_params == {}


def test_host_trailing_slash():
    api = SyncSketchAPI("u", "k", host="https://test.syncsketch.com/")
    assert api.HOST == "https://test.syncsketch.com"


def test_join_url_path():
    assert SyncSketchAPI.join_url_path("abc") == "abc/"
    assert SyncSketchAPI.join_url_path("abc", "123") == "abc/123/"
    assert SyncSketchAPI.join_url_path("abc", "/123/", "/xyz/") == "abc/123/xyz/"


def test_get_api_base_url():
    api = SyncSketchAPI("u", "k", host="https://test.syncsketch.com")
    assert api.get_api_base_url() == "https://test.syncsketch.com/api/v1/"
    assert api.get_api_base_url("v2") == "https://test.syncsketch.com/api/v2/"


def test_backward_compat_aliases():
    # In Python 2, class attribute access wraps functions in unbound methods,
    # so we compare via __func__ when available, otherwise direct identity.
    def get_fn(attr):
        return getattr(attr, "__func__", attr)

    assert get_fn(SyncSketchAPI.isConnected) is get_fn(SyncSketchAPI.is_connected)
    assert get_fn(SyncSketchAPI.getAccounts) is get_fn(SyncSketchAPI.get_accounts)
    assert get_fn(SyncSketchAPI.getProjects) is get_fn(SyncSketchAPI.get_projects)
    assert get_fn(SyncSketchAPI.addProject) is get_fn(SyncSketchAPI.create_project)
    assert get_fn(SyncSketchAPI.addReview) is get_fn(SyncSketchAPI.create_review)
    assert get_fn(SyncSketchAPI.getItem) is get_fn(SyncSketchAPI.get_item)
    assert get_fn(SyncSketchAPI.addMedia) is get_fn(SyncSketchAPI.add_media)
    assert get_fn(SyncSketchAPI.getCurrentUser) is get_fn(SyncSketchAPI.get_current_user)


if __name__ == "__main__":
    tests = [
        test_default_auth,
        test_expiring_token_auth,
        test_header_auth,
        test_host_trailing_slash,
        test_join_url_path,
        test_get_api_base_url,
        test_backward_compat_aliases,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print("  PASS  %s" % test.__name__)
        except Exception as e:
            failed += 1
            print("  FAIL  %s: %s" % (test.__name__, e))

    print("\n%d passed, %d failed (Python %s)" % (passed, failed, sys.version.split()[0]))
    sys.exit(1 if failed else 0)
