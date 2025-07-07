# -*- coding: utf-8 -*-
# @Author: floepi
# @Date:   2015-06-04 17:42:44
# @Last Modified by: Brady Endres
# @Last Modified time: 2025-07-07

from __future__ import absolute_import, division, print_function

import json
import mimetypes
import os
import time
from io import open

import requests

try:
    # Python 2
    from urllib import urlencode
except ImportError:
    # Python 3
    from urllib.parse import urlencode

# Import appropriate threading/queue modules for Python 2/3 compatibility
try:
    # Python 3
    from queue import Queue
    from concurrent.futures import ThreadPoolExecutor
except ImportError:
    # Python 2
    from Queue import Queue
    import threading

    # Define a simple ThreadPoolExecutor-like class for Python 2
    class ThreadPoolExecutor(object):
        def __init__(self, max_workers):
            self.max_workers = max_workers
            self.tasks = Queue()
            self.results = {}
            self.workers = []

        def submit(self, fn, *args, **kwargs):
            task_id = len(self.results)
            self.tasks.put((task_id, fn, args, kwargs))
            self.results[task_id] = None
            return task_id

        def _worker(self):
            while not self.tasks.empty():
                try:
                    task_id, fn, args, kwargs = self.tasks.get(block=False)
                    self.results[task_id] = fn(*args, **kwargs)
                except:
                    pass

        def __enter__(self):
            for _ in range(self.max_workers):
                worker = threading.Thread(target=self._worker)
                worker.daemon = True
                worker.start()
                self.workers.append(worker)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            for worker in self.workers:
                worker.join()

        def result(self, task_id):
            return self.results.get(task_id)


# NOTE - PLEASE INSTALL THE REQUEST MODULE FOR UPLOADING MEDIA
# http://docs.python-requests.org/en/latest/user/install/#install


class SyncSketchAPI:
    """
    Convenience API to communicate with the SyncSketch Service for collaborative online reviews
    """

    def __init__(
        self,
        auth,
        api_key,
        host="https://www.syncsketch.com",
        useExpiringToken=False,
        debug=False,
        api_version="v1",
        use_header_auth=False,
    ):
        """
        Setup the SyncSketch API class.

        :param str auth: Your email or username
        :param str api_key:: Your SyncSketch API Key, found in the settings tab
        :param str host: Used for testing or local installs
        :param bool useExpiringToken: (Optional) When using the expiring tokens for authentication. Expiring tokens are generated behind a authenticated URL like https://syncsketch.com/users/getToken/ which returns JSON when the authentication is successful
        :param bool debug: (Optional) Print debug information
        :param str api_version: (Optional) The version of the API to use
        :param bool use_header_auth: (Optional) Use header authentication instead of query parameters
        :return: SyncSketchAPI
        :rtype: SyncSketchAPI
        """
        # set initial values
        self.user_auth = auth
        self.api_key = api_key
        self.api_params = dict()
        self.headers = dict()
        auth_type = "apikey"

        if useExpiringToken:
            auth_type = "token"

        if use_header_auth:
            # This will be the preferred way to connect once we fix headers on live
            self.headers = {
                "Authorization": "{auth_type} {auth}:{key}".format(
                    auth_type=auth_type, auth=self.user_auth, key=self.api_key
                )
            }
        elif useExpiringToken:
            self.api_params = {"token": self.api_key, "email": self.user_auth}
        else:
            self.api_params = {"api_key": self.api_key, "username": self.user_auth}

        self.api_version = api_version
        self.debug = debug
        self.HOST = host.rstrip("/")

    def get_api_base_url(self, api_version=None):
        return self.join_url_path(self.HOST, "/api/{}/".format(api_version or self.api_version))

    @staticmethod
    def join_url_path(base, *path_segments):
        """Takes one more more strings and returns a properly terminated url path. Handles strings regardless
        of whether they are "/" prefixed/terminated or not.

        >>> SyncSketchAPI.join_url_path("abc")
        "abc/"
        >>> SyncSketchAPI.join_url_path("abc", "123")
        "abc/123/"
        >>> SyncSketchAPI.join_url_path("abc", "123", "/xyz/")
        "abc/123/xyz/"

        :param str base: The "base" path to append to.
        :param path_segments: Additional strings to be appened to the path.
        :type path_segments: List[str]
        :returns: A "/" terminated string containing base and path_segments delimited by "/".
        """
        # remove preceeding "/" from entries to avoid absolute path behavior with os.path.join
        # and append an empty string so that os.path.join will add a terminating "/" if needed
        path_segments = [base.rstrip("/")] + [path_segment.strip("/") for path_segment in path_segments] + [""]

        return "/".join(path_segments)

    def _get_unversioned_api_url(self, path):
        if "http" in path:
            # If the path is already a full URL, return it as is
            return path
        return self.join_url_path(self.HOST, path)

    def _get_json_response(
        self,
        url,
        method=None,
        getData=None,
        postData=None,
        patchData=None,
        putData=None,
        content_type="application/json",
        raw_response=False,
    ):
        url = self._get_unversioned_api_url(url)

        params = self.api_params.copy()

        # Update headers with custom content-type
        headers = self.headers.copy()
        headers["Content-Type"] = content_type

        if getData:
            params.update(getData)

        method = method or "get"
        if postData or method == "post":
            method = "post"
            r = requests.post(
                url,
                params=params,
                data=json.dumps(postData) if postData else None,
                headers=headers,
            )
        elif patchData or method == "patch":
            method = "patch"
            r = requests.patch(url, params=params, json=patchData, headers=headers)
        elif putData or method == "put":
            method = "put"
            r = requests.put(url, params=params, json=putData, headers=headers)
        elif method == "delete":
            r = requests.delete(url, params=params, headers=headers)
        else:
            r = requests.get(url, params=params, headers=headers)

        if self.debug:
            print(
                "{method} URL: {url}, params: {params}, headers: {headers}, status_code: {status_code}".format(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    status_code=r.status_code,
                )
            )

        if raw_response:
            # Return the whole response object, not {"objects": []}
            return r

        try:
            return r.json()
        except Exception as e:
            if self.debug:
                print(e)

            print("Error: %s" % r.text)

            return {"objects": []}

    @staticmethod
    def _update_params(key, value, params):
        if value:
            if isinstance(value, (list, tuple)):
                value = ",".join(value)

            params.update({key: value})

    def is_connected(self, raw_response=True):
        """
        Convenience function to check if the API is connected to SyncSketch
        Will check against Status Code 200 and return False if not which most likely would be
        and authorization error

        :return: Connection success
        :rtype: bool
        """
        url = "/api/v1/person/connected/"
        params = self.api_params.copy()

        if self.debug:
            print("URL: %s, params: %s" % (url, params))

        r = self._get_json_response(url, raw_response=raw_response)

        if raw_response:
            return r
        return r.status_code == 200

    def get_tree(self, withItems=False, raw_response=False):
        """
        Get nested tree of account, projects, reviews and optionally items for the current user

        :param bool withItems: Include items in the response
        :param bool raw_response: Get whole response from REST API.
        :return: Tree data
        :rtype: dict
        """
        get_params = {"fetchItems": 1} if withItems else {}
        return self._get_json_response("/api/v1/person/tree/", getData=get_params, raw_response=raw_response)

    """
    Workspace / Account
    """

    def get_accounts(self, fields=None, raw_response=False):
        """
        Get a list of workspaces the user has access to

        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: List of workspaces the user has access to
        :rtype: list[dict]
        """
        get_params = {"active": 1}
        self._update_params("fields", fields, get_params)

        return self._get_json_response("/api/v1/account/", getData=get_params, raw_response=raw_response)

    def update_account(self, account_id, data, raw_response=False):
        """
        Update a workspace / account

        :param int account_id: the id of the item
        :param dict data: normal dict with data for item
        :param bool raw_response: Get whole response from REST API.
        :return: Workspace / Account data
        :rtype: dict
        """
        if not isinstance(data, dict):
            print("Please make sure you pass a dict as data")
            return False

        return self._get_json_response(
            "/api/v1/account/%s/" % account_id,
            patchData=data,
            raw_response=raw_response,
        )

    """
    Projects
    """

    def create_project(self, account_id, name, description="", data=None, raw_response=False):
        """
        Add a project to your account. Please make sure to pass the accountId which you can query using the getAccounts command.

        :param int account_id: id of the account to connect with
        :param str name: Name of the project
        :param str description: Description of the project
        :param dict data: additional information e.g is_public. Find out more about available fields at /api/v1/project/schema/.
        :param bool raw_response: Get whole response from REST API.
        :return: Project data
        :rtype: dict
        """
        if data is None:
            data = {}

        post_data = {
            "name": name,
            "description": description,
            "account_id": account_id,
        }

        post_data.update(data)

        return self._get_json_response("/api/v1/project/", postData=post_data, raw_response=raw_response)

    def get_projects(
        self,
        include_deleted=False,
        include_archived=False,
        include_tags=False,
        include_connections=False,
        limit=100,
        offset=0,
        fields=None,
        raw_response=False,
    ):
        """
        Get a list of currently active projects the user has access to

        :param bool include_deleted: if true, include deleted projects
        :param bool include_archived: if true, include archived projects
        :param bool include_tags: if true, include tag list on the project object
        :param bool include_connections: if true, include full user connections on the project object
        :param int limit: limit the number of results
        :param int offset: offset the results
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: Dict with meta information and an array of found projects
        :rtype: list[dict]
        """
        get_params = {
            "active": 1,
            "is_archived": 0,
            "account__active": 1,
            "limit": limit,
            "offset": offset,
        }

        self._update_params("fields", fields, get_params)

        if include_connections:
            get_params["withFullConnections"] = True

        if include_deleted:
            del get_params["active"]

        if include_archived:
            del get_params["active"]
            del get_params["is_archived"]

        if include_tags:
            get_params["include_tags"] = 1

        return self._get_json_response("/api/v1/project/", getData=get_params, raw_response=raw_response)

    def get_projects_by_name(self, name, fields=None, raw_response=False):
        """
        Get a list of projects by name

        :param str name: Name to search for
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: List of projects
        :rtype: list[dict]
        """
        get_params = {"name__istartswith": name}
        self._update_params("fields", fields, get_params)

        return self._get_json_response("/api/v1/project/", getData=get_params, raw_response=raw_response)

    def get_project_by_id(self, project_id, fields=None, raw_response=False):
        """
        Get single project by id

        :param int project_id: Project id
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: Project data
        :rtype: dict
        """
        get_params = {}
        self._update_params("fields", fields, get_params)

        return self._get_json_response(
            "/api/v1/project/%s/" % project_id,
            getData=get_params,
            raw_response=raw_response,
        )

    def get_project_storage(self, project_id, raw_response=False):
        """
        Get project storage usage in bytes

        .. code:: python

            # Example response
            {'storage': 12345}

        :param int project_id: Project ID
        :param bool raw_response: Get whole response from REST API.
        :return: Storage usage in bytes
        :rtype: dict[str, int]
        """
        return self._get_json_response("/api/v2/project/%s/storage/" % project_id, raw_response=raw_response)

    def update_project(self, project_id, data, raw_response=False):
        """
        Update a project

        :param int project_id: the id of the item
        :param dict data: dict with new data for item
        :param bool raw_response: Get whole response from REST API.
        :return: updated project data
        :rtype: dict
        """
        if not isinstance(data, dict):
            print("Please make sure you pass a dict as data")
            return False

        return self._get_json_response(
            "/api/v1/project/%s/" % project_id,
            patchData=data,
            raw_response=raw_response,
        )

    def delete_project(self, project_id, raw_response=False):
        """
        Delete a project by id.

        :param int project_id: Project ID to delete
        :param bool raw_response: Get whole response from REST API.
        :return:
        """
        return self._get_json_response(
            "/api/v1/project/%s/" % project_id,
            patchData=dict(active=False),
            raw_response=raw_response,
        )

    def duplicate_project(
        self,
        project_id,
        name=None,
        copy_reviews=False,
        copy_users=False,
        copy_settings=False,
        raw_response=False,
    ):
        """
        Create a new project from an existing project

        :param int project_id: Source project id
        :param str name: New project name
        :param bool copy_reviews: Whether to copy reviews (without items)
        :param bool copy_users: Whether to copy users
        :param bool copy_settings: Whether to copy settings
        :param bool raw_response: Get whole response from REST API.
        :return: New project data
        :rtype: dict[str, Any]
        """

        config = dict(
            reviews=copy_reviews,
            users=copy_users,
            settings=copy_settings,
        )
        if name:
            config["name"] = name

        return self._get_json_response(
            "/api/v2/project/%s/duplicate/" % project_id,
            postData=config,
            raw_response=raw_response,
        )

    def archive_project(self, project_id, raw_response=False):
        """
        Archive a project

        :param int project_id:
        :param bool raw_response: Get whole response from REST API.
        :return: Project data
        :rtype: dict
        """

        return self._get_json_response(
            "/api/v1/project/%s/" % project_id,
            patchData=dict(is_archived=True),
            raw_response=raw_response,
        )

    def restore_project(self, project_id, raw_response=False):
        """
        Restore (unarchive) a project

        :param int project_id:
        :param bool raw_response: Get whole response from REST API.
        :return: Project data
        :rtype: dict
        """

        return self._get_json_response(
            "/api/v1/project/%s/" % project_id,
            patchData=dict(is_archived=False),
            raw_response=raw_response,
        )

    """
    Reviews
    """

    def create_review(self, project_id, name, description="", data=None, raw_response=False):
        """
        Add a review to a project

        :param int project_id:
        :param str name:
        :param str description:
        :param dict data:
        :param bool raw_response: Get whole response from REST API.
        :return: Review data
        :rtype: dict
        """
        if data is None:
            data = {}

        postData = {
            "project": "/api/%s/project/%s/" % (self.api_version, project_id),
            "name": name,
            "description": description,
        }

        postData.update(data)

        return self._get_json_response("/api/v1/review/", postData=postData, raw_response=raw_response)

    def get_reviews_by_project_id(self, project_id, limit=100, offset=0, fields=None, raw_response=False):
        """
        Get list of reviews by project id.

        .. code:: python

            # Example response
            {
                "meta": {...},
                "objects": [...]
            }

        :param int project_id: SyncSketch project id
        :param int limit: Limit the number of results
        :param int offset: Offset the results
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: Dict with meta information and an array of found projects
        :rtype: dict
        """
        get_params = {
            "project__id": project_id,
            "project__active": 1,
            "project__is_archived": 0,
            "limit": limit,
            "offset": offset,
        }
        self._update_params("fields", fields, get_params)

        return self._get_json_response("/api/v1/review/", getData=get_params, raw_response=raw_response)

    def get_review_by_name(self, name, limit=100, offset=0, fields=None, raw_response=False):
        """
        Get list of reviews by name using a case insensitive startswith query

        :param str name: Name of the review
        :param int limit: Limit the number of results
        :param int offset: Offset the results
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: Dict with meta information and an array of found projects
        """
        get_params = {
            "name__istartswith": name,
            "active": True,
            "limit": limit,
            "offset": offset,
        }
        self._update_params("fields", fields, get_params)

        return self._get_json_response("/api/v1/review/", getData=get_params, raw_response=raw_response)

    def get_review_by_id(self, review_id, fields=None, raw_response=False):
        """
        Get single review by id.

        :param review_id: Number
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: Review Data
        :rtype: dict
        """
        get_params = {}
        self._update_params("fields", fields, get_params)
        return self._get_json_response(
            "/api/v1/review/%s/" % review_id,
            getData=get_params,
            raw_response=raw_response,
        )

    def get_review_by_uuid(self, uuid, fields=None, raw_response=False):
        """
        Get single review by uuid.
        UUID can be found in the review URL e.g. syncsketch.com/sketch/<uuid>/

        :param str uuid: UUID of the review.
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: Review dict
        :rtype: dict
        """
        get_params = {"uuid": uuid}
        self._update_params("fields", fields, get_params)

        response = self._get_json_response("/api/v1/review/", getData=get_params, raw_response=raw_response)

        if raw_response:
            return response

        if "objects" in response and len(response["objects"]) > 0:
            return response["objects"][0]
        return None

    def get_review_storage(self, review_id, raw_response=False):
        """
        Get review storage usage in bytes

        :param int review_id: Review ID
        :param bool raw_response: Get whole response from REST API.
        :return: Storage usage in bytes
        :rtype: dict[str, int]
        """
        return self._get_json_response("/api/v2/review/%s/storage/" % review_id, raw_response=raw_response)

    def update_review(self, review_id, data, raw_response=False):
        """
        Update a review

        :param int review_id: the id of the item
        :param dict data: dict with data for item
        :param bool raw_response: Get whole response from REST API.
        :return: updated review data
        :rtype: dict
        """
        if not isinstance(data, dict):
            print("Please make sure you pass a dict as data")
            return False

        return self._get_json_response("/api/v1/review/%s/" % review_id, patchData=data, raw_response=raw_response)

    def sort_review_items(self, review_id, items, raw_response=False):
        """
        Update a review

        Example `items` param

        .. code:: python

            items = [{
                "id": 1, # item id
                "sortorder": 0, # sortorder, starting at 0
            }]

        Method output example:

        .. code:: python

            # number of successful items sort updated
            { "updated_items": int }

        :param int review_id: the id of the item
        :param list items: payload
        :param bool raw_response: Get whole response from REST API.
        :return: response
        :rtype: dict
        """
        if not isinstance(items, list):
            print("Please make sure you pass a list as data")
            return False

        return self._get_json_response(
            "/api/v2/review/%s/sort_items/" % review_id,
            putData=dict(items=items),
            raw_response=raw_response,
        )

    def archive_review(self, review_id, raw_response=True):
        """
        Archive a review

        :param int review_id:
        :param bool raw_response: Get whole response from REST API.
        :return: Response object
        """

        return self._get_json_response(
            "/api/v2/review/%s/archive/" % review_id,
            method="post",
            raw_response=raw_response,
        )

    def restore_review(self, review_id, raw_response=True):
        """
        Restore (unarchive) a review

        :param int review_id:
        :param bool raw_response: Get whole response from REST API.
        :return: Response object
        """

        return self._get_json_response(
            "/api/v2/review/%s/restore/" % review_id,
            method="post",
            raw_response=raw_response,
        )

    def delete_review(self, review_id, raw_response=False):
        """
        Delete a review by id.

        :param int review_id: Review ID to delete
        :param bool raw_response: Get whole response from REST API.
        :return: Review data
        :rtype: dict
        """
        return self._get_json_response(
            "/api/v1/review/%s/" % review_id,
            patchData=dict(active=False),
            raw_response=raw_response,
        )

    def create_review_section(self, review_id, name, item_ids, uuid=None, raw_response=False):
        """
        Create a new review section

        :param int review_id: Review ID
        :param str name: Section name
        :param list item_ids: List of item IDs to add to the section
        :param str uuid: Optional UUID for the section
        :param bool raw_response: Get whole response from REST API.
        :return: Section data
        :rtype: dict
        """
        postData = {
            "name": name,
            "itemIds": item_ids,
        }

        if uuid:
            postData["uuid"] = uuid

        return self._get_json_response(
            "/api/v2/review/{}/sections/create/".format(review_id),
            postData=postData,
            raw_response=raw_response,
        )

    def update_review_sections(self, review_id, data, raw_response=False):
        """
        Update one or more review sections

        .. code:: python

            # Example data
            sections_to_update = [
                {
                    "uuid": "section-uuid",
                    "name": "New Section Name",
                    "itemIds": [1, 2, 3],
                }
            ]

        :param int review_id: Review ID
        :param list[dict] data: Section data
        :param bool raw_response: Get whole response from REST API.
        :return: Section data
        :rtype: dict
        """
        return self._get_json_response(
            "/api/v2/review/{}/sections/bulk-update/".format(review_id),
            method="put",
            putData=data,
            raw_response=raw_response,
        )

    def delete_review_section(self, review_id, section_uuid, raw_response=False):
        """
        Delete a review section

        :param int review_id: Review ID
        :param str section_uuid: Section UUID
        :param bool raw_response: Get whole response from REST API.
        :return: Section data
        :rtype: dict
        """
        return self._get_json_response(
            "/api/v2/review/{}/sections/{}/".format(review_id, section_uuid),
            method="delete",
            raw_response=raw_response,
        )

    """
    Items
    """

    def get_item(self, item_id, data=None, fields=None, raw_response=False):
        """
        Get single item by id

        :param int item_id:
        :param dict data:
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: Item data
        :rtype: dict
        """
        get_params = data if data else {}
        self._update_params("fields", fields, get_params)

        return self._get_json_response(
            "/api/v1/item/{}/".format(item_id),
            getData=get_params,
            raw_response=raw_response,
        )

    def update_item(self, item_id, data, raw_response=False):
        """
        Update an item

        :param int item_id: the id of the item
        :param dict data: dict with data for item
        :param bool raw_response: Get whole response from REST API.
        :return: updated item data
        :rtype: dict
        """
        if not isinstance(data, dict):
            print("Please make sure you pass a dict as data")
            return False

        return self._get_json_response("/api/v1/item/%s/" % item_id, patchData=data, raw_response=raw_response)

    def add_item(self, review_id, name, fps, additional_data, raw_response=False):
        """
        create a media item record and connect it to a review. This should be used in case you want to add items with externaly hosted
        media by passing in the external_url and external_thumbnail_url to the additionalData dict e.g

        .. code:: python

            additionalData = {
                external_url: http://52.24.98.51/wp-content/uploads/2017/03/rain.jpg
                external_thumbnail_url: http://52.24.98.51/wp-content/uploads/2017/03/rain.jpg
            }

        or

        .. code:: python

            additionalData = {
                width:1024
                height:720
                artist: "Brady Endres"
                duration:3 (in seconds)
                description: the description here
                size: size in byte
                type: image | video
            }

        NOTE: you always need to pass in FPS for SyncSketch to work!

        For a complete list of available fields to set, please
        visit https://www.syncsketch.com/api/v1/item/schema/

        :param int review_id: Required review_id
        :param str name: Name of the item
        :param float fps: The frame per second is very important for syncsketch to determine the correct number of frames
        :param dict additional_data: dictionary with item info
        :param bool raw_response: Get whole response from REST API.
        :return: Item data
        :rtype: dict
        """

        postData = {
            "reviewId": review_id,
            "status": "done",
            "fps": fps,
            "name": name,
        }

        postData.update(additional_data)

        return self._get_json_response("/api/v1/item/", postData=postData, raw_response=raw_response)

    def add_media(
        self,
        review_id,
        filepath,
        artist_name="",
        file_name="",
        noConvertFlag=False,
        itemParentId=False,
    ):
        """
        Convenience function to upload a file to a review. It will automatically create
        an Item and attach it to the review. NOTE - if you are hosting your own media, please
        use the addItem function and pass in the external_url and external_thumbnail_url

        :param int review_id: Required review_id
        :param str filepath: path for the file on disk e.g /tmp/movie.webm
        :param str artist_name: The name of the artist you want associated with this media file
        :param str file_name: The name of the file. Please make sure to pass the correct file extension
        :param bool noConvertFlag: the video you are uploading is already in a browser compatible format
        :param int itemParentId: (Optional) set when you want to add a new version of an item. itemParentId is the id of the item you want to upload a new version for
        :return: Item data
        :rtype: dict
        """
        get_params = self.api_params.copy()

        if noConvertFlag:
            get_params.update({"noConvertFlag": 1})

        if itemParentId:
            get_params.update({"itemParentId": itemParentId})

        uploadURL = "%s/items/uploadToReview/%s/?%s" % (
            self.HOST,
            review_id,
            urlencode(get_params),
        )

        files = {"reviewFile": open(filepath, "rb")}
        r = requests.post(
            uploadURL,
            files=files,
            data=dict(artist=artist_name, name=file_name),
            headers=self.headers,
        )

        if self.debug:
            print("URL: %s, params: %s" % (uploadURL, get_params))

        try:
            return json.loads(r.text)
        except Exception:
            print(r.text)

    def add_media_by_url(self, review_id, media_url, artist_name="", noConvertFlag=False):
        """
        Convenience function to upload a mediaURl to a review. Please use this function when you already have your files in the cloud, e.g
        AWS, Dropbox, Shotgrid, etc...

        We will automatically create an Item and attach it to the review.

        :param int review_id: Required review_id
        :param str media_url: url to the media you are trying to upload
        :param str artist_name: The name of the artist you want associated with this media file
        :param bool noConvertFlag: the video you are uploading is already in a browser compatible format and does not need to be converted
        :return: Item data
        :rtype: dict
        """
        get_params = self.api_params.copy()

        if not review_id or not media_url:
            raise Exception("You need to pass a review id and a media_url")

        if noConvertFlag:
            get_params.update({"noConvertFlag": 1})

        upload_url = "%s/items/uploadToReview/%s/?%s" % (
            self.HOST,
            review_id,
            urlencode(get_params),
        )

        r = requests.post(
            upload_url,
            {"media_url": media_url, "artist": artist_name},
            headers=self.headers,
        )

        try:
            return json.loads(r.text)
        except Exception:
            print(r.text)

    def upload_file(
        self,
        review_id,
        filepath,
        file_name="",
        item_uuid=None,
        noConvertFlag=False,
        chunk_size=5 * 1024 * 1024,
        max_workers=None,
    ):
        """
        Upload a file to a review using multipart upload.
        This uses direct to s3 multipart upload to upload large files in chunks.

        :param int review_id: Required review_id
        :param str filepath: Path for the file on disk e.g /tmp/movie.webm
        :param str file_name: The name of the file. Please make sure to pass the correct file extension
        :param str item_uuid: Optional UUID for the item. If not provided, a new one will be generated by the server
        :param bool noConvertFlag: The video you are uploading is already in a browser compatible format
        :param int chunk_size: Size of each chunk in bytes for multipart upload (default: 5MB)
        :param int max_workers: Maximum number of parallel upload workers (default: auto-detected based on system capabilities)
        :return: A dict containing item information including "id" and "uuid" or None on failure
        :rtype: Optional[dict]
        """
        if not self.headers:
            print("upload_file failed. use_header_auth must be set to true.")
            return None

        # Determine optimal number of workers based on system capabilities
        if max_workers is None:
            try:
                import multiprocessing

                cpu_count = multiprocessing.cpu_count()
                # Set max_workers based on CPU count, but capped between 2 and 8
                # For network-bound operations, we don't want to overload with too many threads
                max_workers = max(2, min(cpu_count * 2, 8))
                if self.debug:
                    print(
                        "Auto-detected {max_workers} workers based on {cpu_count} CPU cores".format(
                            max_workers=max_workers, cpu_count=cpu_count
                        )
                    )
            except (ImportError, NotImplementedError):
                # Fall back to 4 if we can't determine CPU count
                max_workers = 4
                if self.debug:
                    print("Could not detect CPU count, defaulting to 4 workers")

        # Get file information
        file_size = os.stat(filepath).st_size
        if not file_name:
            file_name = os.path.basename(filepath)
        elif not os.path.splitext(file_name)[1]:
            file_name += os.path.splitext(filepath)[1]

        content_type = mimetypes.guess_type(filepath, strict=False)[0]

        # Step 1: Start the upload process
        start_upload_data = {
            "review_id": review_id,
            "item_name": file_name,
            "item_data": {
                "upload_type": "s3",
                "uuid": item_uuid,
                "size": file_size,
                "content_type": content_type,
            },
        }

        start_upload_response = self._get_json_response(
            url="/uploads/stats/upload-start/",
            method="post",
            postData=start_upload_data,
            raw_response=True,
        )

        if not start_upload_response.ok:
            print("Failed to start multipart upload: {}".format(start_upload_response.text))
            return None

        start_upload_data = start_upload_response.json()

        item_id = start_upload_data.get("item_id")

        # The server may generate and return a UUID if one was not provided
        item_uuid = start_upload_data.get("item_uuid", item_uuid)

        # Step 2: Initialize multipart upload
        multipart_init_data = {
            "review_id": review_id,
            "item_data": {
                "name": file_name,
                "uuid": item_uuid,
                "noConvertFlag": noConvertFlag,
                "size": file_size,
                "content_type": content_type,
            },
        }

        multipart_response = self._get_json_response(
            url="/uploads/multipart-upload/",
            method="post",
            postData=multipart_init_data,
            raw_response=True,
        )

        if not multipart_response.ok:
            print("Failed to initialize multipart upload: {}".format(multipart_response.text))
            return None

        multipart_data = multipart_response.json()

        # Extract necessary information for uploading parts
        upload_id = multipart_data.get("uploadId")
        upload_key = multipart_data.get("key")

        if not all([upload_id, upload_key]):
            print("Missing required multipart upload information")
            return None

        # Step 3: Prepare chunks for parallel upload
        chunks = []
        with open(filepath, "rb") as f:
            part_number = 1
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunks.append((part_number, chunk))
                part_number += 1

        total_parts = len(chunks)
        if self.debug:
            print("Prepared {total_parts} chunks for parallel upload".format(total_parts=total_parts))

        # Define function to upload a single part with retry
        def upload_part(part_number, chunk_data):
            max_retries = 3
            retry_delay = 1  # Start with 1 second delay

            for attempt in range(1, max_retries + 1):
                try:
                    # Request a signed URL for this part
                    sign_part_url = "/uploads/multipart-upload/{upload_id}/sign-part/{part_number}/".format(
                        upload_id=upload_id, part_number=part_number
                    )

                    sign_part_response = self._get_json_response(
                        url=sign_part_url,
                        method="get",
                        getData={"key": upload_key},
                        raw_response=True,
                    )

                    if not sign_part_response.ok:
                        if self.debug:
                            print(
                                "Attempt {attempt}: Failed to get signed URL for part {part_number}: {response_text}".format(
                                    attempt=attempt,
                                    part_number=part_number,
                                    response_text=sign_part_response.text,
                                )
                            )
                        if attempt < max_retries:
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        return None

                    part_url = sign_part_response.json().get("url")
                    if not part_url:
                        if self.debug:
                            print(
                                "Attempt {attempt}: No signed URL returned for part {part_number}".format(
                                    attempt=attempt,
                                    part_number=part_number,
                                )
                            )
                        if attempt < max_retries:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                        return None

                    # Upload the part
                    part_response = requests.put(
                        part_url,
                        data=chunk_data,
                        headers={"Content-Type": content_type},
                    )

                    if not part_response.ok:
                        if self.debug:
                            print(
                                "Attempt {attempt}: Failed to upload part {part_number}: {response_text}".format(
                                    attempt=attempt,
                                    part_number=part_number,
                                    response_text=part_response.text,
                                )
                            )
                        if attempt < max_retries:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                        return None

                    # Get the ETag from the response headers
                    etag = part_response.headers.get("ETag")
                    if not etag:
                        if self.debug:
                            print(
                                "Attempt {attempt}: No ETag returned for part {part_number}".format(
                                    attempt=attempt,
                                    part_number=part_number,
                                )
                            )
                        if attempt < max_retries:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                        return None

                    # If we get here, the upload was successful
                    if self.debug:
                        print(
                            "Successfully uploaded part {part_number} of {total_parts}".format(
                                part_number=part_number, total_parts=total_parts
                            )
                            + (" on attempt {}".format(attempt) if attempt > 1 else "")
                        )

                    return {"PartNumber": part_number, "ETag": etag}

                except Exception as e:
                    if self.debug:
                        print(
                            "Attempt {attempt}: Exception uploading part {part_number}: {exc}".format(
                                attempt=attempt,
                                part_number=part_number,
                                exc=str(e),
                            )
                        )
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    return None

            # If we get here, all retries failed
            return None

        # Step 4: Upload parts in parallel
        uploaded_parts = []
        failed = False

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            # Submit all upload tasks
            for part_number, chunk in chunks:
                future = executor.submit(upload_part, part_number, chunk)
                futures.append((part_number, future))

            # Collect results
            for part_number, future in futures:
                try:
                    # For Python 3's ThreadPoolExecutor
                    result = future.result() if hasattr(future, "result") else executor.result(future)

                    if result is None:
                        print("Failed to upload part {part_number}".format(part_number=part_number))
                        failed = True
                        break

                    uploaded_parts.append(result)
                except Exception as e:
                    print("Error uploading part {part_number}: {exc}".format(part_number=part_number, exc=str(e)))
                    failed = True
                    break

        if failed or len(uploaded_parts) != total_parts:
            print("Failed to upload all parts successfully. Aborting upload.")
            # Abort the multipart upload
            abort_url = "/uploads/multipart-upload/{upload_id}/abort/".format(upload_id=upload_id)
            abort_response = self._get_json_response(
                url=abort_url,
                method="post",
                getData={"key": upload_key},
                raw_response=True,
            )

            if not abort_response.ok and self.debug:
                print("Failed to abort multipart upload: {}".format(abort_response.text))

            return None

        # Sort parts by part number to ensure correct order
        uploaded_parts.sort(key=lambda x: x["PartNumber"])

        # Step 5: Complete the multipart upload
        complete_url = "/uploads/multipart-upload/{upload_id}/complete/".format(upload_id=upload_id)
        complete_data = {"parts": uploaded_parts}

        complete_response = self._get_json_response(
            url=complete_url,
            method="post",
            getData={"key": upload_key},
            postData=complete_data,
            raw_response=True,
        )

        if not complete_response.ok:
            print("Failed to complete multipart upload: {}".format(complete_response.text))
            return None

        # Get the item data
        return self.get_item(item_id)

    def add_media_v2(self, review_id, filepath, file_name="", item_uuid=None, noConvertFlag=False):
        """
        Similar to add_media method, but uploads the media file directly to SyncSketche's internal S3 instead of to
        the SyncSketch server. In some cases, using this method over add_media can improve upload performance and
        stability. Unlike add_media this method does not return as much data about the created item.

        :param int review_id: Required review_id.
        :param str filepath: path for the file on disk e.g /tmp/movie.webm.
        :param str file_name: The name of the file. Please make sure to pass the correct file extension.
        :param bool noConvertFlag: the video you are uploading is already in a browser compatible format.
        :return: A dict, containing "item_id" and "uuid" or None on failure.
        :rtype: Optional[dict]
        """
        if not self.headers:
            print("add_media_via_s3 failed. use_header_auth must be set to true.")
            return None

        content_length = os.stat(filepath).st_size

        # for media > 5gb use v1 upload api
        if content_length > 5 * 1000 * 1000:
            result = self.add_media_v1(
                review_id=review_id,
                filepath=filepath,
                file_name=file_name,
                noConvertFlag=noConvertFlag,
            )
            return {"id": result["id"], "uuid": result["uuid"]}

        content_type = mimetypes.guess_type(filepath, strict=False)[0]

        url_response = self._get_s3_signed_url(
            review_id=review_id,
            item_name=file_name,
            item_uuid=item_uuid,
            content_length=content_length,
            content_type=content_type,
            no_convert=noConvertFlag,
        )

        if not url_response.ok:
            print("Failed to generate signed S3 url.\nAPI response:\n{}".format(url_response.text))
            return None

        url_response_data = url_response.json()
        url = url_response_data["url"]
        fields = url_response_data["fields"]

        with open(filepath, "rb") as file:
            upload_response = requests.post(url, data=fields, files={"file": file})

        if not upload_response.ok:
            print("Upload process failed while uploading file to S3.\nS3 response:\n{}".format(upload_response.text))
            return None

        return {
            "id": fields["x-amz-meta-item-id"],
            "uuid": fields["x-amz-meta-item-uuid"],
        }

    def _get_s3_signed_url(
        self,
        review_id,
        item_name,
        item_uuid=None,
        content_type=None,
        content_length=None,
        no_convert=False,
        raw_response=True,
    ):
        """
        Internal method. Use to retrieve s3 signed url for file upload in `add_media_via_s3`.
        """
        request_data = self.api_params.copy()
        additional_request_data = {
            "review_id": review_id,
            "item_name": item_name,
            "item_data": {
                "uuid": item_uuid,
                "content_type": content_type,
                "content_length": content_length,
                "noConvertFlag": no_convert,
            },
        }
        request_data.update(additional_request_data)

        request_url = "{}/uploads/get-s3-signed-url/".format(self.HOST)

        return self._get_json_response(
            url=request_url,
            postData=request_data,
            raw_response=raw_response,
        )

    def get_media(self, searchCriteria, fields=None, raw_response=False):
        """
        This is a general search function. You can search media items by

        - 'id'
        - 'name'
        - 'status'
        - 'active'
        - 'creator': ALL_WITH_RELATIONS, <-- these are foreign key queries
        - 'reviews': ALL_WITH_RELATIONS, <-- these are foreign key queries
        - 'created' using 'exact', 'range', 'gt', 'gte', 'lt', 'lte'

        To query items by foreign keys please use the foreign key syntax described in the Django search definition:
        https://docs.djangoproject.com/en/1.11/topics/db/queries/

        If you want to query by "review name" for example you would pass in

        reviews__name = NAME TO SEARCH

        Using the "__" syntax you can even search for items by project like

        reviews__project__name = $PROJECT NAME TO SEARCH

        To speed up a query you can also pass in a limit e.g limit:10

        .. code:: python

            results = s.getMedia({'reviews__project__name':'test', 'limit': 1, 'active': 1})

        NOTE: Please make sure to include the active:1 query if you only want active media. Deleted files are currently
        only deactivated and kept for a certain period of time before they are "purged" from the system.

        :param dict searchCriteria: Search params
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: List of media items
        :rtype: list[dict]
        """
        self._update_params("fields", fields, searchCriteria)

        return self._get_json_response("/api/v1/item/", getData=searchCriteria, raw_response=raw_response)

    def get_items_by_review_id(self, review_id, fields=None, raw_response=False):
        """
        Get all items in a review

        :param int review_id: Review ID
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: List of media items
        :rtype: list[dict]
        """
        get_params = {"reviews__id": review_id, "active": 1}
        self._update_params("fields", fields, get_params)
        return self._get_json_response("/api/v1/item/", getData=get_params, raw_response=raw_response)

    def delete_item(self, item_id, raw_response=False):
        """
        Delete a item by id.

        :param int item_id: Item ID to delete
        :param bool raw_response: Get whole response from REST API.
        :return:
        """
        return self._get_json_response(
            "/api/v1/item/{}/".format(item_id),
            patchData=dict(active=False),
            raw_response=raw_response,
        )

    def bulk_delete_items(self, item_ids, raw_response=True):
        """
        Delete multiple items by id.

        :param list[int] item_ids: List of item IDs to delete
        :param bool raw_response: Get whole response from REST API.
        :return:
        """
        return self._get_json_response(
            "/api/v2/bulk-delete-items/",
            postData=dict(item_ids=item_ids),
            method="post",
            raw_response=raw_response,
        )

    def connect_item_to_review(self, item_id, review_id):
        print("DEPRECATED.")
        print("A new improved method for this will be added soon.")
        return "Deprecated"

    def move_items(self, new_review_id, item_data, raw_response=True):
        """
        Move items from one review to another

        item_data should be a list of dictionaries with the old review id and the item id.
        The items in the list will be moved to the new review for the param new_review_id

        .. code:: python

            # Example item_data
            # review_id is the current review an item is in
            # it will be moved to the new_review_id
            items_to_move = [
                {"review_id": 1, "item_id": 1},
                {"review_id": 1, "item_id": 2},
                {"review_id": 1, "item_id": 3},
            ]

        :param int new_review_id: The review id to move the items to
        :param list[dict] item_data: List of dictionaries with the old review id and the item id
        :param bool raw_response: Get whole response from REST API.
        :return:
        """

        return self._get_json_response(
            "/api/v2/move-review-items/",
            method="post",
            postData={"new_review_id": new_review_id, "item_data": item_data},
            raw_response=raw_response,
        )

    """
    Frames (Sketches / Comments)
    """

    def add_comment(self, item_id, text, review_id, frame=0, raw_response=False):
        """
        Add a comment to an item

        :param int item_id: Item to add the comment to
        :param str text: Comment text
        :param int review_id: Review you are adding the comment to
        :param int frame: Frame number of the video to add the comment to (if applicable)
        :param bool raw_response: Get whole response from REST API.
        :return:
        """
        item = self.get_item(item_id, data={"review_id": review_id})

        # Ugly method of getting revision id from item data, should fix this with api v2
        revision_id = item.get("revision_id")
        if not revision_id:
            return "error"

        post_data = dict(
            item="/api/v1/item/{}/".format(item_id),
            frame=frame,
            revision="/api/v1/revision/{}/".format(revision_id),
            type="comment",
            text=text,
        )

        return self._get_json_response(
            "/api/v1/frame/",
            method="post",
            postData=post_data,
            raw_response=raw_response,
        )

    def get_annotations(self, item_id, revisionId=False, review_id=False, raw_response=False):
        """
        Get sketches and comments for an item. Frames have a revision id which signifies a "set of notes".
        When querying an item you'll get the available revisions for this item. If you wish to get only the latest
        revision, please get the revisionId for the latest revision.

        :param int item_id: id of the media item you are querying.
        :param int revisionId: Optional revisionId to narrow down the results
        :param int review_id: RECOMMENDED - retrieve annotations for a specific review only.
        :param bool raw_response: Get whole response from REST API.
        :return: dict
        """
        get_params = {"item__id": item_id, "active": 1}

        if revisionId:
            get_params["revision__id"] = revisionId

        if review_id:
            get_params["revision__review_id"] = review_id

        return self._get_json_response("/api/v1/frame/", getData=get_params, raw_response=raw_response)

    def get_flattened_annotations(
        self,
        review_id,
        item_id,
        with_tracing_paper=False,
        return_as_base64=False,
        raw_response=False,
    ):
        """
        Returns a list of sketches either as signed urls from s3 or base64 encoded strings.
        The sketches are composited over the background frame of the item.

        :param int review_id: Review ID
        :param int item_id: Item ID
        :param bool with_tracing_paper: Include tracing paper in the response
        :param bool return_as_base64: Return sketches as base64 encoded strings
        :param bool raw_response: Get whole response from REST API.
        :return: List of sketches as signed urls from s3 or base64 encoded strings
        """
        get_data = {
            "include_data": 1,
            "tracingpaper": 1 if with_tracing_paper else 0,
            "base64": 1 if return_as_base64 else 0,
            "async": 1,
        }
        get_data.update(self.api_params)

        url = "{}/api/v2/downloads/flattenedSketches/{}/{}/".format(self.HOST, review_id, item_id)

        r = requests.post(url, params=get_data, headers=self.headers)
        celery_task_id = r.json()

        if self.debug:
            print("Flattened annotations download started with celery task ID: %s", celery_task_id)

        # check the celery task
        request_processing = True
        check_celery_url = "{host}/api/v2/downloads/flattenedSketches/{celery_task_id}/".format(
            host=self.HOST, celery_task_id=celery_task_id
        )

        r = requests.get(check_celery_url, params=self.api_params, headers=self.headers)

        while request_processing:
            if self.debug:
                print("Checking celery task status at: %s" % check_celery_url)

            result = r.json()

            if result.get("status") == "done":
                return result

            if result.get("status") == "failed":
                return None

            # wait a bit
            time.sleep(1)

            # check the url again
            r = requests.get(check_celery_url, params=self.api_params, headers=self.headers)
        return

    def get_grease_pencil_overlays(self, review_id, item_id, homedir=None):
        """
        Download overlay sketches for Maya Greasepencil.

        Download overlay sketches for Maya Greasepencil. Function will download
        a zip file which contains an XML and the sketches as png files. Maya
        can load the zip file to overlay the sketches over the 3D model!

        For more information visit:
        https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2015/ENU/Maya/files/Grease-Pencil-Tool-htm.html

        PLEASE make sure that /tmp is writable

        :param int review_id: Review ID
        :param int item_id: Item ID
        :param str homedir: Optional path to download the zip file to
        :return: filePath to the zip file with the greasePencil data.
        """
        url = "%s/api/v2/downloads/greasePencil/%s/%s/" % (
            self.HOST,
            review_id,
            item_id,
        )
        r = requests.post(url, params=self.api_params, headers=self.headers)
        celery_task_id = r.json()

        if self.debug:
            print("Grease Pencil download started with celery task ID: %s", celery_task_id)

        # check the celery task
        request_processing = True
        check_celery_url = "%s/api/v2/downloads/greasePencil/%s/" % (
            self.HOST,
            celery_task_id,
        )

        r = requests.get(check_celery_url, params=self.api_params, headers=self.headers)

        while request_processing:
            if self.debug:
                print("Checking celery task status at: %s" % check_celery_url)

            result = r.json()

            if result.get("status") == "done":
                data = result.get("data")

                # storing locally
                local_filename = "/tmp/%s.zip" % data["fileName"]
                if homedir:
                    local_filename = os.path.join(homedir, "{}.zip".format(data["fileName"]))
                r = requests.get(data["s3Path"], stream=True)
                with open(local_filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)

                request_processing = False
                return local_filename

            if result.get("status") == "failed":
                request_processing = False
                return False

            # wait a bit
            time.sleep(1)

            # check the url again
            r = requests.get(check_celery_url, params=self.api_params, headers=self.headers)
        return

    """
    Users
    """

    def add_users(self, project_id, users, raw_response=False):
        """
        Deprecated method.
        """
        print("Deprecated - please use method add_users_to_project instead")

        return self.add_users_to_project(project_id=project_id, users=users, raw_response=raw_response)

    def get_users_by_name(self, name, fields=None, raw_response=False):
        """
        Name is a combined search and will search in first_name, last_name and email

        :param str name: Name to search for
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: List of users
        :rtype: list[dict]
        """
        get_params = {"name": name}
        self._update_params("fields", fields, get_params)
        return self._get_json_response("/api/v1/simpleperson/", getData=get_params, raw_response=raw_response)

    def get_user_by_email(self, email, fields=None, raw_response=True):
        """
        Get user by email

        :param str email: Email to search for
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: User data
        :rtype: dict
        """
        get_params = {"email__iexact": email}
        self._update_params("fields", fields, get_params)
        response = self._get_json_response("/api/v1/simpleperson/", getData=get_params, raw_response=raw_response)

        try:
            data = response.json()
            return data.get("objects")[0]
        except:
            return None

    def get_users_by_project_id(self, project_id, raw_response=False):
        """
        Get all users in a project

        :param int project_id:
        :param bool raw_response: Get whole response from REST API.
        :return: List of users
        :rtype: list[dict]
        """
        return self._get_json_response(
            "/api/v2/all-project-users/{}/".format(project_id),
            raw_response=raw_response,
        )

    def get_connections_by_user_id(
        self,
        user_id,
        account_id,
        include_inactive=None,
        include_archived=None,
        raw_response=False,
    ):
        """
        Get all project and account connections for a user. Good for checking access for a user that might have left...

        :param int user_id: User ID to get connections for
        :param int account_id: Account ID to get connections for
        :param bool include_inactive: Include inactive projects
        :param bool include_archived: Include archived projects
        :param bool raw_response: Get whole response from REST API.
        :return: List of connections
        :rtype: list[dict]
        """
        data = {}
        if include_inactive is not None:
            data["include_inactive"] = "true" if include_inactive else "false"
        if include_archived is not None:
            data["include_archived"] = "true" if include_archived else "false"
        return self._get_json_response(
            "/api/v2/user/{}/connections/account/{}/".format(user_id, account_id),
            getData=data,
            raw_response=raw_response,
        )

    def get_user_by_id(self, user_id, fields=None, raw_response=False):
        """
        Get a user by ID

        :param int user_id:
        :param list|str|int|bool fields: fields to fetch from backend
        :param bool raw_response: Get whole response from REST API.
        :return: User data
        :rtype: dict
        """
        get_params = {}
        self._update_params("fields", fields, get_params)
        return self._get_json_response(
            "/api/v1/simpleperson/%s/" % user_id,
            getData=get_params,
            raw_response=raw_response,
        )

    def get_current_user(self, raw_response=False):
        return self._get_json_response("/api/v1/simpleperson/currentUser/", raw_response=raw_response)

    def add_users_to_workspace(self, workspace_id, users, note="", raw_response=False):
        """
        Add Users to Workspace

        .. code:: python

            users=[{"email":"test@test.de","permission":"admin"}]

        :param int workspace_id: id of the workspace
        :param list users: list of new users - possible permissions "admin", "manager"
        :param str note: (Optional) message for the invitation email
        :param bool raw_response: Get whole response from REST API.
        :return: response
        """
        if not isinstance(users, list):
            print("Please add users by list with user items e.g users=[{'email':'test@test.de','permission':'admin'}]")
            return False

        post_data = {
            "which": "account",
            "entity_id": workspace_id,
            "note": note,
            "users": json.dumps(users),
        }

        return self._get_json_response("/api/v2/add-users/", postData=post_data, raw_response=raw_response)

    def remove_users_from_workspace(self, workspace_id, users, raw_response=False):
        """
        Remove a list of users from a workspace
        Can remove by id or email

        .. code:: python

            users=[{"email":"test@test.de"}, {"id":12345}]

        :param int workspace_id: id of the workspace
        :param list users: list of users to remove - either remove by user email or id
        :param bool raw_response: Get whole response from REST API.
        :return: response
        """
        if not isinstance(users, list):
            print("Please add users by list with user items e.g users=[{'email':'test@test.de'}]")
            return False

        post_data = {
            "which": "account",
            "entity_id": workspace_id,
            "users": json.dumps(users),
        }

        return self._get_json_response("/api/v2/remove-users/", postData=post_data, raw_response=raw_response)

    def add_users_to_project(self, project_id, users, note="", raw_response=False):
        """
        Add Users to Project

        possible permissions

        - admin
        - member
        - viewer
        - reviewer

        .. code:: python

            users=[{"email":"test@test.de","permission":"viewer"}]

        :param int project_id: id of the project
        :param list[dict] users: list of new users
        :param str note: (Optional) message for the invitation email
        :param bool raw_response: Get whole response from REST API.
        :return: response
        """
        if not isinstance(users, list):
            print(
                "Please add users by list with user items e.g users=[{'email':'test@test.de','permission':'viewer'}]"
            )
            return False

        post_data = {
            "which": "project",
            "entity_id": project_id,
            "note": note,
            "users": json.dumps(users),
        }

        return self._get_json_response("/api/v2/add-users/", postData=post_data, raw_response=raw_response)

    def remove_users_from_project(self, project_id, users, raw_response=False):
        """
        Remove a list of users from a project

        remove by user email or id

        .. code:: python

            users=[{"email":"test@test.de"}, {"id":12345}]

        :param int project_id: id of the project
        :param list users: list of users to remove - either remove by user email or id
        :param bool raw_response: Get whole response from REST API.
        """
        if not isinstance(users, list):
            print("Please add users by list with user items e.g users=[{'email':'test@test.de']")
            return False

        post_data = {
            "which": "project",
            "entity_id": project_id,
            "users": json.dumps(users),
        }

        return self._get_json_response("/api/v2/remove-users/", postData=post_data, raw_response=raw_response)

    """
    Shotgrid API
    """

    def shotgrid_get_projects(self, syncsketch_project_id):
        """
        Returns list of Shotgrid projects connected to your account

        :param int syncsketch_project_id: SyncSketch project id
        """
        print("DEPRECATED!  Please use Shotgrid's API")
        print("https://github.com/shotgunsoftware/python-api")

        raise DeprecationWarning("DEPRECATED!  Please use Shotgrid's API.")

    def shotgrid_create_config(
        self,
        syncsketch_account_id,
        syncsketch_project_id=None,
        data=None,
        raw_response=True,
    ):
        """
        Create a new Shotgrid configuration for a SyncSketch workspace and optionally a project

        :param int syncsketch_account_id:
        :param int syncsketch_project_id:
        :param dict data: Configuration data.
        :param bool raw_response: Get whole response from REST API.
        :return:
        """
        assert isinstance(data, dict), "Please make sure you pass a dict as data"
        assert "url" in data, "Please make sure you pass a Shotgrid url in the data"
        assert "username" in data, "Please make sure you pass a username in the data"
        assert "key" in data, "Please make sure you pass a script user key in the data"

        post_data = {
            "account": syncsketch_account_id,
            "project": syncsketch_project_id,
        }
        post_data.update(data)

        test_data = {"test_settings": post_data}

        test_response = self._get_json_response(
            "/api/v2/shotgun/config/test/",
            postData=test_data,
            raw_response=raw_response,
        )
        if test_response.status_code == 200:
            return self._get_json_response("/api/v2/shotgun/config/", postData=post_data, raw_response=raw_response)
        else:
            raise Exception("Shotgrid configuration test failed. Please check your Shotgrid config settings.")

    def shotgrid_get_playlists(
        self,
        syncsketch_account_id,
        syncsketch_project_id,
        shotgun_project_id=None,
        raw_response=False,
    ):
        """
        Returns list of Shotgrid playlists modified in the last 120 days
        If the syncsketch project is directly linked to a shotgrid by the workspace admin, the
        param shotgun_project_id will be ignored and can be omitted during the function call

        :param int syncsketch_account_id: SyncSketch account id
        :param int syncsketch_project_id: SyncSketch project id
        :param int shotgun_project_id: (optional) Shotgrid project id
        :param bool raw_response: Get whole response from REST API.
        :return: list of Shotgrid playlists
        """
        url = "/api/v2/shotgun/playlists/{}/".format(syncsketch_account_id)
        if syncsketch_project_id:
            url = self.join_url_path(url, "/{}/".format(syncsketch_project_id))

        data = {"shotgun_project_id": shotgun_project_id}
        return self._get_json_response(url, method="get", getData=data, raw_response=raw_response)

    def shotgrid_sync_review_notes(self, review_id, raw_response=False):
        """
        Sync notes from SyncSketch review to the original shotgrid playlist
        Returns task id to use in get_shotgun_sync_review_notes_progress to get progress

        returns dict with information about the REST API call:

        - message=<STR> "Shotgrid review notes sync started"
        - status=<STR> processing/done/failed
        - progress_url=<STR> Full url to call for progress/results
        - task_id=<STR> task_ids pass this value to the get_shotgun_sync_review_items_progress function
        - percent_complete=<INT> 0-100 value of percent complete
        - total_items=<INT> number of items being synced from shotgrid
        - remaining_items=<INT> number of items not yet pulled from shotgrid

        :param int review_id: SyncSketch review id
        :param bool raw_response: Get whole response from REST API.
        :return: Progress information
        :rtype: dict
        """
        url = "/api/v2/shotgun/sync-review-notes/review/{}/".format(review_id)

        return self._get_json_response(url, method="post", raw_response=raw_response)

    def shotgrid_sync_new_item_notes(self, project_id, review_id, item_id, raw_response=False):
        """
        Sync new notes from SyncSketch review item to the original shotgrid playlist
        Returns dict with information about the REST API call

        - sketch_upload_error=<BOOL> "True in case of error"
        - sketches=<INT> "Number of sketches synced"
        - comments=<INT> "Number of comments synced"
        - attachments=<INT> "Number of attachments synced"
        - item_name=<STR> "Name of item that was synced"

        :param int project_id: SyncSketch project id
        :param int review_id: SyncSketch review id
        :param int item_id: SyncSketch item id
        :param bool raw_response: Get whole response from REST API.
        :return:
        """
        url = "/api/v2/shotgun/sync-notes/project/{}/review/{}/{}/".format(project_id, review_id, item_id)

        return self._get_json_response(url, method="post", raw_response=raw_response)

    def get_shotgrid_sync_review_notes_progress(self, task_id, raw_response=False):
        """
        Returns status of review notes sync for the task id provided in shotgun_sync_review_notes

        Returns a dict with the following keys:

        - message=<STR> "Shotgrid review notes sync started"
        - status=<STR> processing/done/failed
        - progress_url=<STR> Full url to call for progress/results
        - task_id=<STR> task_ids pass this value to the get_shotgun_sync_review_items_progress function
        - percent_complete=<INT> 0-100 value of percent complete
        - total_items=<INT> number of items being synced from shotgrid
        - remaining_items=<INT> number of items not yet pulled from shotgrid

        :param str task_id: UUID of the task returned by shotgrid_sync_review_notes
        :param bool raw_response: Get whole response from REST API.
        :return: Progress information
        :rtype: dict
        """
        url = "/api/v2/shotgun/sync-review-notes/{}/".format(task_id)

        return self._get_json_response(url, method="get", raw_response=raw_response)

    def shotgrid_sync_review_items(self, syncsketch_project_id, playlist_code, playlist_id, review_id=None):
        """
        Create or update SyncSketch review with shotgrid playlist items
        Returns task id to use in get_shotgun_sync_review_items_progress to get progress

        Response format:

        - message=<STR> "Shotgrid review item sync started",
        - status=<STR> processing/done/failed,
        - progress_url=<STR> Full url to call for progress/results,
        - task_id=<STR> task_ids - pass this value to the get_shotgun_sync_review_items_progress function,
        - percent_complete=<INT> 0-100 value of percent complete,
        - total_items=<INT> number of items being synced from shotgrid,
        - remaining_items=<INT> number of items not yet pulled from shotgrid,
        - data=<dict>
        -    review_id=<INT> review.id,
        -    review_link=<STR> url link to the syncsketch player with the review pulled from shotgrid,

        :param int syncsketch_project_id:
        :param str playlist_code:
        :param int playlist_id:
        :param int review_id: (optional)
        :return:
        :rtype: dict
        """
        url = "/api/v2/shotgun/sync-items/project/{}/".format(syncsketch_project_id)
        if review_id:
            url = self.join_url_path(url, "/review/{}/check/".format(review_id))
        else:
            url = self.join_url_path(url, "/check/")

        data = {"playlist_code": playlist_code, "playlist_id": playlist_id}

        response = self._get_json_response(url, method="post", postData=data)
        if self.debug:
            print(response)

        result = dict(
            review_id=response["review_id"],
            items=[],
            status="done",
            total_items=len(response["items"]),
        )

        if "items" in response:
            for item in response["items"]:
                data = {"playlist_item_json": json.dumps(item)}
                item_sync_url = "/api/v2/shotgun/sync-items/project/{}/review/{}/".format(
                    syncsketch_project_id, response["review_id"]
                )
                item_data = self._get_json_response(item_sync_url, method="post", postData=data)
                result["items"].append(item_data["id"])

                if self.debug:
                    print(item_data)
        return result

    def get_shotgrid_sync_review_items_progress(self, task_id):
        """
        Returns status of review items sync for the task id provided in shotgun_sync_review_items

        :param str task_id: UUID of the task returned by shotgrid_sync_review_items
        :returns: DeprecationWarning
        :rtype: dict
        """
        raise DeprecationWarning("DEPRECATED!  Response is printed in the shotgrid_sync_review_items() function")

    # alias methods to <name>_v1 if they have a v2
    add_media_v1 = add_media
    # Keep old names for backwards compatibility
    isConnected = is_connected
    getAccounts = get_accounts
    getProjects = get_projects
    getProjectsByName = get_projects_by_name
    getProjectById = get_project_by_id
    addProject = create_project
    deleteProject = delete_project
    addReview = create_review
    getReviewsByProjectId = get_reviews_by_project_id
    getReviewByName = get_review_by_name
    getReviewById = get_review_by_id
    getItem = get_item
    addItem = add_item
    updateItem = update_item
    addMedia = add_media
    addMediaByURL = add_media_by_url
    getMediaByReviewId = get_items_by_review_id
    get_media_by_review_id = get_items_by_review_id
    getMedia = get_media
    connectItemToReview = connect_item_to_review
    deleteReview = delete_review
    deleteItem = delete_item
    getUsersByName = get_users_by_name
    getUsersByProjectId = get_users_by_project_id
    getUserById = get_user_by_id
    addUsers = add_users
    getCurrentUser = get_current_user
    addComment = add_comment
    getGreasePencilOverlays = get_grease_pencil_overlays
    getTree = get_tree
    getAnnotations = get_annotations
    get_shotgun_sync_review_items_progress = get_shotgrid_sync_review_items_progress
    shotgun_sync_review_items = shotgrid_sync_review_items
    get_shotgun_sync_review_notes_progress = get_shotgrid_sync_review_notes_progress
    shotgun_sync_new_item_notes = shotgrid_sync_new_item_notes
    shotgun_sync_review_notes = shotgrid_sync_review_notes
    shotgun_get_playlists = shotgrid_get_playlists
    shotgun_create_config = shotgrid_create_config
    shotgun_get_projects = shotgrid_get_projects
