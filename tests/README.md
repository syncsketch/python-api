# SyncSketch API Tests

Unit tests for the SyncSketch Python API using **pytest** with mocked HTTP via the **responses** library.
These tests are not a true reflection of the live API behavior but are designed to validate the client-side logic and ensure consistent behavior across Python versions.

## Setup

```bash
pip install -e ".[test]"

# Install tox
pip install tox
```

## Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=syncsketch --cov-report=term-missing

# Single file
pytest tests/test_projects.py -v
```

## Multi-version Testing (tox)

```bash
# All configured Python versions (3.7-3.13)
tox

# Specific version
tox -e py313
```

Requires the target Python versions to be installed (e.g. via pyenv). Missing interpreters are skipped automatically.

## Python 2.7 Smoke Test

The full pytest suite requires Python 3.8+. For Python 2.7, a standalone smoke test is provided that verifies import, construction, and core utilities without any test framework dependencies.

```bash
# Requires only the `requests` package installed for Python 2.7
python2.7 tests/test_py27_smoke.py
```

### Running via Docker

If you don't have Python 2.7 or 3.7 installed locally, you can use Docker:

```bash
# Python 2.7 smoke tests
docker run --rm -v "$(pwd)":/app -w /app python:2.7 sh -c \
  'pip install "requests>=2.20.0,<2.28.0" && python tests/test_py27_smoke.py'

# Python 3.7+ full test suite (replace tag with desired version)
docker run --rm -v "$(pwd)":/app -w /app python:3.7 sh -c \
  'pip install -e ".[test]" && pytest tests/ -v'
```

## Test Structure

| File | Covers |
|------|--------|
| `conftest.py` | Shared fixtures, sample data, helpers |
| `test_auth.py` | Constructor and 3 auth modes (query param, expiring token, header) |
| `test_get_json_response.py` | Core HTTP dispatch, auth injection, response parsing |
| `test_connection.py` | `is_connected`, URL utilities, `_update_params` |
| `test_accounts.py` | Workspace/account CRUD |
| `test_projects.py` | Project CRUD, archive/restore, duplicate |
| `test_reviews.py` | Review CRUD, sections, archive/restore |
| `test_items.py` | Item CRUD, bulk delete, move |
| `test_media_upload.py` | `add_media`, `add_media_v2`, `upload_file` multipart S3 flow |
| `test_annotations.py` | Comments, annotations, grease pencil overlays |
| `test_users.py` | User lookup, workspace/project user management |
| `test_shotgrid.py` | ShotGrid config, sync, deprecation |
| `test_tree.py` | `get_tree` |
| `test_backward_compat.py` | camelCase backward-compatibility alias checks |

## Mocking Approach

All HTTP calls are intercepted at the `requests` transport layer using the [responses](https://github.com/getsentry/responses) library. This catches both calls through `_get_json_response()` and direct `requests.*` calls in upload/annotation methods. File I/O and `time.sleep` in polling loops are patched with `unittest.mock`.
