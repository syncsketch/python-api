# -*- coding: utf-8 -*-
"""Summary"""
# @Author: floepi
# @Date:   2015-06-04 17:42:44
# @Last Modified by: Brady Endres
# @Last Modified time: 2024-04-04
#!/usr/local/bin/python

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
except:
    # Python 3
    from urllib.parse import urlencode


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
        """Summary

        Args:
            user_auth (str): Your email or username
            api_key (str): Your SyncSketch API Key, found in the settings tab
            host (str): Used for testing or local installs
            useExpiringToken (bool, optional): When using the expiring tokens for authentication.
            Expiring tokens are generated behind a authenticated URL like https://syncsketch.com/users/getToken/
            which returns JSON when the authentication is successful
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
        self.HOST = host

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
            r = requests.post(url, params=params, data=json.dumps(postData), headers=headers)
        elif patchData or method == "patch":
            method = "patch"
            r = requests.patch(url, params=params, json=patchData, headers=headers)
        elif putData or method == "put":
            method = "put"
            r = requests.put(url, params=params, json=putData, headers=headers)
        elif method == "delete":
            method = "delete"
            r = requests.patch(url, params=params, data={"active": False}, headers=headers)
        else:
            r = requests.get(url, params=params, headers=headers)

        if self.debug:
            print("%s URL: %s, params: %s" % (method, url, params))

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

    def is_connected(self):
        """
        Convenience function to check if the API is connected to SyncSketch
        Will check against Status Code 200 and return False if not which most likely would be
        and authorization error
        :return:
        """
        url = "/api/v1/person/connected/"
        params = self.api_params.copy()

        if self.debug:
            print("URL: %s, params: %s" % (url, params))

        r = self._get_json_response(url, raw_response=True)
        return r.status_code == 200

    def get_tree(self, withItems=False):
        """
            get nested tree of account, projects, reviews and optionally items for the current user
        :param withItems:
        :return:
        """
        get_params = {"fetchItems": 1} if withItems else {}
        return self._get_json_response("/api/v1/person/tree/", getData=get_params)

    """
    Accounts
    """

    def get_accounts(self):
        """Summary

        Returns:
            TYPE: Account
        """
        get_params = {"active": 1}
        return self._get_json_response("/api/v1/account/", getData=get_params)

    def update_account(self, account_id, data):
        """
        Update a project

        Args:
            account_id (TYPE): the id of the item
            data (dict): normal dict with data for item

        Returns:
            TYPE: item
        """
        if not isinstance(data, dict):
            print("Please make sure you pass a dict as data")
            return False

        return self._get_json_response("/api/v1/account/%s/" % account_id, patchData=data)

    """
    Projects
    """

    def create_project(self, account_id, name, description="", data=None):
        """
        Add a project to your account. Please make sure to pass the accountId which you can query using the getAccounts command.

        :param int account_id: id of the account to connect with
        :param str name: Name of the project
        :param description: String
        :param dict data: additional information e.g is_public. Find out more about available fields at /api/v1/project/schema/.
        :return:
        """
        if data is None:
            data = {}

        post_data = {
            "name": name,
            "description": description,
            "account_id": account_id,
        }

        post_data.update(data)

        return self._get_json_response("/api/v1/project/", postData=post_data)

    def get_projects(
        self,
        include_deleted=False,
        include_archived=False,
        include_tags=False,
        include_connections=False,
        limit=100,
        offset=0,
    ):
        """
        Get a list of currently active projects

        :param include_deleted: boolean: if true, include deleted projects
        :param include_archived: boolean: if true, include archived projects
        :param include_tags: boolean: if true, include tag list on the project object

        Returns:
            TYPE: Dict with meta information and an array of found projects
        """
        get_params = {
            "active": 1,
            "is_archived": 0,
            "account__active": 1,
            "limit": limit,
            "offset": offset,
        }

        if include_connections:
            get_params["withFullConnections"] = True

        if include_deleted:
            del get_params["active"]

        if include_archived:
            del get_params["active"]
            del get_params["is_archived"]

        if include_tags:
            get_params["include_tags"] = 1

        return self._get_json_response("/api/v1/project/", getData=get_params)

    def get_projects_by_name(self, name):
        """
        Get a project by name regardless of status

        Returns:
            TYPE: Dict with meta information and an array of found projects
        """
        get_params = {"name__istartswith": name}
        return self._get_json_response("/api/v1/project/", getData=get_params)

    def get_project_by_id(self, project_id):
        """
        Get single project by id
        :param project_id: Number
        :return:
        """
        return self._get_json_response("/api/v1/project/%s/" % project_id)

    def get_project_storage(self, project_id):
        """
        Get project storage usage in bytes
        :param project_id: Number
        :return:
        """
        return self._get_json_response("/api/v2/project/%s/storage/" % project_id)

    def update_project(self, project_id, data):
        """
        Update a project

        Args:
            project_id (TYPE): the id of the item
            data (dict): normal dict with data for item

        Returns:
            TYPE: item
        """
        if not isinstance(data, dict):
            print("Please make sure you pass a dict as data")
            return False

        return self._get_json_response("/api/v1/project/%s/" % project_id, patchData=data)

    def delete_project(self, project_id):
        """
        Get single project by id.
        :param project_id: Number
        :return:
        """
        return self._get_json_response("/api/v1/project/%s/" % project_id, patchData=dict(active=False))

    def duplicate_project(
        self,
        project_id,
        name=None,
        copy_reviews=False,
        copy_users=False,
        copy_settings=False,
    ):
        """
        Create a new project from an existing project

        :param project_id: Int
        :param name: Str
        :param copy_reviews: Bool
        :param copy_users: Bool
        :param copy_settings: Bool
        :return: New project data
        """

        config = dict(
            reviews=copy_reviews,
            users=copy_users,
            settings=copy_settings,
        )
        if name:
            config["name"] = name

        return self._get_json_response("/api/v2/project/%s/duplicate/" % project_id, postData=config)

    def archive_project(self, project_id):
        """
        Archive a project

        :param int project_id:
        :return:
        """

        return self._get_json_response("/api/v1/project/%s/" % project_id, patchData=dict(is_archived=True))

    def restore_project(self, project_id):
        """
        Restore (unarchive) a project

        :param int project_id:
        :return:
        """

        return self._get_json_response("/api/v1/project/%s/" % project_id, patchData=dict(is_archived=False))

    """
    Reviews
    """

    def create_review(self, project_id, name, description="", data=None):
        if data is None:
            data = {}

        postData = {
            "project": "/api/%s/project/%s/" % (self.api_version, project_id),
            "name": name,
            "description": description,
        }

        postData.update(data)

        return self._get_json_response("/api/v1/review/", postData=postData)

    def get_reviews_by_project_id(self, project_id, limit=100, offset=0):
        """
        Get list of reviews by project id.
        :param project_id: Number
        :return: Dict with meta information and an array of found projects
        """
        get_params = {
            "project__id": project_id,
            "project__active": 1,
            "project__is_archived": 0,
            "limit": limit,
            "offset": offset,
        }
        return self._get_json_response("/api/v1/review/", getData=get_params)

    def get_review_by_name(self, name):
        """
        Get reviews by name using a case insensitive startswith query
        :param name: String - Name of the review
        :return: Dict with meta information and an array of found projects
        """
        get_params = {"name__istartswith": name}
        return self._get_json_response("/api/v1/review/", getData=get_params)

    def get_review_by_id(self, review_id):
        """
        Get single review by id.
        :param review_id: Number
        :return: Review Dict
        """
        return self._get_json_response("/api/v1/review/%s/" % review_id)

    def get_review_by_uuid(self, uuid):
        """
        Get single review by uuid.
        :param uuid:
        :return: Review dict
        """
        data = self._get_json_response("/api/v1/review/", getData={"uuid": uuid})
        if "objects" in data and len(data["objects"]) > 0:
            return data["objects"][0]
        return None

    def get_review_storage(self, review_id):
        """
        Get review storage usage in bytes
        :param review_id: Number
        :return:
        """
        return self._get_json_response("/api/v2/review/%s/storage/" % review_id)

    def update_review(self, review_id, data):
        """
        Update a review

        Args:
            review_id (TYPE): the id of the item
            data (dict): normal dict with data for item

        Returns:
            TYPE: item
        """
        if not isinstance(data, dict):
            print("Please make sure you pass a dict as data")
            return False

        return self._get_json_response("/api/v1/review/%s/" % review_id, patchData=data)

    def sort_review_items(self, review_id, items):
        """
        Update a review

        Args:
            review_id (TYPE): the id of the item
            items (list): payload
                e.g.
                [
                    {
                        "id": 1, # item id
                        "sortorder": 0, # sortorder, starting at 0
                    }
                ]

        Returns:
            TYPE: dict
                { "updated_items": int }  # number of successful items sort updated
        """
        if not isinstance(items, list):
            print("Please make sure you pass a list as data")
            return False

        return self._get_json_response("/api/v2/review/%s/sort_items/" % review_id, putData=dict(items=items))

    def archive_review(self, review_id):
        """
        Archive a review

        :param int review_id:
        :return: empty response
        """

        return self._get_json_response("/api/v2/review/%s/archive/" % review_id, method="post", raw_response=True)

    def restore_review(self, review_id):
        """
        Restore (unarchive) a review

        :param int review_id:
        :return: empty response
        """

        return self._get_json_response("/api/v2/review/%s/restore/" % review_id, method="post", raw_response=True)

    def delete_review(self, review_id):
        """
        Get single review by id.
        :param review_id: Int
        :return:
        """
        return self._get_json_response("/api/v1/review/%s/" % review_id, patchData=dict(active=False))

    """
    Items
    """

    def get_item(self, item_id, data=None):
        return self._get_json_response("/api/v1/item/{}/".format(item_id), getData=data)

    def update_item(self, item_id, data):
        """Summary

        Args:
            item_id (TYPE): the id of the item
            data (dict): normal dict with data for item

        Returns:
            TYPE: item
        """
        if not isinstance(data, dict):
            print("Please make sure you pass a dict as data")
            return False

        return self._get_json_response("/api/v1/item/%s/" % item_id, patchData=data)

    def add_item(self, review_id, name, fps, additional_data):
        """
        create a media item record and connect it to a review. This should be used in case you want to add items with externaly hosted
        media by passing in the external_url and external_thumbnail_url to the additionalData dict e.g

        additionalData = {
            external_url: http://52.24.98.51/wp-content/uploads/2017/03/rain.jpg
            external_thumbnail_url: http://52.24.98.51/wp-content/uploads/2017/03/rain.jpg
        }

        NOTE: you always need to pass in FPS for SyncSketch to work!

        For a complete list of available fields to set, please
        visit https://www.syncsketch.com/api/v1/item/schema/

        Args:
            review_id (TYPE): Required review_id
            name (TYPE): Name of the item
            fps (TYPE): The frame per second is very important for syncsketch to determine the correct number of frames
            additional_data (TYPE): dictionary with item info like {
                width:1024
                height:720
                artist: "Brady Endres"
                duration:3 (in seconds)
                description: the description here
                size: size in byte
                type: image | video
            }

        Returns:
            TYPE: Item
        """

        postData = {
            "reviewId": review_id,
            "status": "done",
            "fps": fps,
            "name": name,
        }

        postData.update(additional_data)

        return self._get_json_response("/api/v1/item/", postData=postData)

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

        Args:
            review_id (int): Required review_id
            filepath (string): path for the file on disk e.g /tmp/movie.webm
            artist_name (string): The name of the artist you want associated with this media file
            file_name (string): The name of the file. Please make sure to pass the correct file extension
            noConvertFlag (bool): the video you are uploading is already in a browser compatible format
            itemParentId (int): set when you want to add a new version of an item.
                                itemParentId is the id of the item you want to upload a new version for

        Returns:
            TYPE: Description
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

        try:
            return json.loads(r.text)
        except Exception:
            print(r.text)

    def add_media_by_url(self, review_id, media_url, artist_name="", noConvertFlag=False):
        """
            Convenience function to upload a mediaURl to a review. Please use this function when you already have your files in the cloud, e.g
            AWS, Dropbox, Shotgrid, etc...

            We will automatically create an Item and attach it to the review.

        Args:
            review_id (int): Required review_id
            media_url (string): url to the media you are trying to upload
            noConvertFlag (bool): the video you are uploading is already in a browser compatible format and does not need to be converted

        Returns:
            TYPE: Description
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

    def add_media_v2(self, review_id, filepath, file_name="", item_uuid=None, noConvertFlag=False):
        """Similar to add_media method, but uploads the media file directly to SyncSketche's internal S3 instead of to
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

        request_url = "/uploads/get-s3-signed-url/".format(host=self.HOST)

        return self._get_json_response(
            url=request_url,
            postData=request_data,
            raw_response=True,
        )

    def get_media(self, searchCriteria):
        """
        This is a general search function. You can search media items by

        'id'
        'name'
        'status'
        'active'
        'creator': ALL_WITH_RELATIONS, <-- these are foreign key queries
        'reviews': ALL_WITH_RELATIONS, <-- these are foreign key queries
        'created' using 'exact', 'range', 'gt', 'gte', 'lt', 'lte'

        To query items by foreign keys please use the foreign key syntax described in the Django search definition:
        https://docs.djangoproject.com/en/1.11/topics/db/queries/

        If you want to query by "review name" for example you would pass in

        reviews__name = NAME TO SEARCH

        Using the "__" syntax you can even search for items by project like

        reviews__project__name = $PROJECT NAME TO SEARCH

        To speed up a query you can also pass in a limit e.g limit:10

        results = s.getMedia({'reviews__project__name':'test', 'limit': 1, 'active': 1})

        NOTE: Please make sure to include the active:1 query if you only want active media. Deleted files are currently
        only deactivated and kept for a certain period of time before they are "purged" from the system.

        Args:
            searchCriteria (dict): dictionary

        Returns:
            dict: search results
        """

        return self._get_json_response("/api/v1/item/", getData=searchCriteria)

    def get_media_by_review_id(self, review_id):
        """Summary

        Args:
            review_id (TYPE): Description

        Returns:
            TYPE: Description
        """
        get_params = {"reviews__id": review_id, "active": 1}
        return self._get_json_response("/api/v1/item/", getData=get_params)

    def delete_item(self, item_id):
        """
        Get single item by id.
        :param item_id: Int
        :return:
        """
        return self._get_json_response("/api/v1/item/%s/" % item_id, patchData=dict(active=False))

    def bulk_delete_items(self, item_ids):
        """
        Delete multiple items by id.
        :param item_ids: Array[Int}
        """
        return self._get_json_response(
            "/api/v2/bulk-delete-items/",
            postData=dict(item_ids=item_ids),
            method="post",
            raw_response=True,
        )

    def connect_item_to_review(self, item_id, review_id):
        print("DEPRECATED.")
        print("A new improved method for this will be added soon.")
        return "Deprecated"

    def move_items(self, new_review_id, item_data):
        """
        Move items from one review to another

        item_data should be a list of dictionaries with the old review id and the item id.
        The items in the list will be moved to the new review for the param new_review_id

        :param new_review_id: int
        :param item_data: list [ dict { review_id: int, item_id: int} ]
        :return:
        """

        return self._get_json_response(
            "/api/v2/move-review-items/",
            method="post",
            postData={"new_review_id": new_review_id, "item_data": item_data},
            raw_response=True,
        )

    """
    Frames (Sketches / Comments)
    """

    def add_comment(self, item_id, text, review_id, frame=0):
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

        return self._get_json_response("/api/v1/frame/", method="post", postData=post_data)

    def get_annotations(self, item_id, revisionId=False, review_id=False):
        """
        Get sketches and comments for an item. Frames have a revision id which signifies a "set of notes".
        When querying an item you'll get the available revisions for this item. If you wish to get only the latest
        revision, please get the revisionId for the latest revision.
        :param item_id: id of the media item you are querying.
        :param (number) revisionId: Optional revisionId to narrow down the results
        :param (number) review_id: RECOMMENDED - retrieve annotations for a specific review only.
        :return: dict
        """
        get_params = {"item__id": item_id, "active": 1}

        if revisionId:
            get_params["revision__id"] = revisionId

        if review_id:
            get_params["revision__review_id"] = review_id

        return self._get_json_response("/api/v1/frame/", getData=get_params)

    def get_flattened_annotations(self, review_id, item_id, with_tracing_paper=False, return_as_base64=False):
        """
        Returns a list of sketches either as signed urls from s3 or base64 encoded strings.
        The sketches are composited over the background frame of the item.

        :param syncsketch_review_id: <int>
        :param syncsketch_item_id: <int>
        :param with_tracing_paper: <bool>
        :param return_as_base64: <bool>
        """
        getData = {
            "include_data": 1,
            "tracingpaper": 1 if with_tracing_paper else 0,
            "base64": 1 if return_as_base64 else 0,
            "async": 0,
        }

        url = "/api/v2/downloads/flattenedSketches/{}/{}/".format(review_id, item_id)

        return self._get_json_response(url, method="post", getData=getData)

    def get_grease_pencil_overlays(self, review_id, item_id, homedir=None):
        """Download overlay sketches for Maya Greasepencil.

            Download overlay sketches for Maya Greasepencil. Function will download
            a zip file which contains an XML and the sketches as png files. Maya
            can load the zip file to overlay the sketches over the 3D model!

            For more information visit:
            https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2015/ENU/Maya/files/Grease-Pencil-Tool-htm.html

        :return: filePath to the zip file with the greasePencil data.

        PLEASE make sure that /tmp is writable

        """
        url = "%s/api/v2/downloads/greasePencil/%s/%s/" % (
            self.HOST,
            review_id,
            item_id,
        )
        r = requests.post(url, params=self.api_params, headers=self.headers)
        celery_task_id = r.json()

        # check the celery task
        request_processing = True
        check_celery_url = "%s/api/v2/downloads/greasePencil/%s/" % (
            self.HOST,
            celery_task_id,
        )

        r = requests.get(check_celery_url, params=self.api_params, headers=self.headers)

        while request_processing:
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

    """
    Users
    """

    def add_users(self, project_id, users):
        """
        Deprecated method.
        """
        print("Deprecated - please use method add_users_to_project instead")

        return self.add_users_to_project(project_id=project_id, users=users)

    def get_users_by_name(self, name):
        """
        Name is a combined search and will search in first_name, last_name and email
        """
        return self._get_json_response("/api/v1/simpleperson/", getData={"name": name})

    def get_user_by_email(self, email):
        """
        Get user by email
        """
        response = self._get_json_response(
            "/api/v1/simpleperson/", getData={"email__iexact": email}, raw_response=True
        )

        try:
            data = response.json()
            return data.get("objects")[0]
        except:
            return None

    def get_users_by_project_id(self, project_id):
        return self._get_json_response("/api/v2/all-project-users/{}/".format(project_id))

    def get_connections_by_user_id(self, user_id, account_id, include_inactive=None, include_archived=None):
        """
        Get all project and account connections for a user. Good for checking access for a user that might have left...
        """
        data = {}
        if include_inactive is not None:
            data["include_inactive"] = "true" if include_inactive else "false"
        if include_archived is not None:
            data["include_archived"] = "true" if include_archived else "false"
        return self._get_json_response(
            "/api/v2/user/{}/connections/account/{}/".format(user_id, account_id),
            getData=data,
        )

    def get_user_by_id(self, userId):
        return self._get_json_response("/api/v1/simpleperson/%s/" % userId)

    def get_current_user(self):
        return self._get_json_response("/api/v1/simpleperson/currentUser/")

    def add_users_to_workspace(self, workspace_id, users, note=""):
        """Add Users to Workspace

        Args:
            workspace_id (Number): id of the workspace
            users (List): list with dicts e.g users=[{"email":"test@test.de","permission":"admin"}] - possible permissions "admin"
            note (String): Optional message for the invitation email

        Returns:
            TYPE: Description
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

        return self._get_json_response("/api/v2/add-users/", postData=post_data)

    def remove_users_from_workspace(self, workspace_id, users):
        """Remove a list of users from a workspace

        Args:
            workspace_id (Number): id of the workspace
            users (List): list with dicts e.g users=[{"email":"test@test.de"}, {"id":12345}] - either remove by user email or id

        """
        if not isinstance(users, list):
            print("Please add users by list with user items e.g users=[{'email':'test@test.de'}]")
            return False

        post_data = {
            "which": "account",
            "entity_id": workspace_id,
            "users": json.dumps(users),
        }

        return self._get_json_response("/api/v2/remove-users/", postData=post_data)

    def add_users_to_project(self, project_id, users, note=""):
        """Add Users to Project

        Args:
            project_id (Number): id of the project
            users (List): list with dicts e.g users=[{"email":"test@test.de","permission":"viewer"}] - possible permissions "admin, member, viewer or reviewer"
            note (String): Optional message for the invitation email

        Returns:
            TYPE: Description
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

        return self._get_json_response("/api/v2/add-users/", postData=post_data)

    def remove_users_from_project(self, project_id, users):
        """Remove a list of users from a project

        Args:
            project_id (Number): id of the project
            users (List): list with dicts e.g users=[{"email":"test@test.de"}, {"id":12345}] - either remove by user email or id

        """
        if not isinstance(users, list):
            print("Please add users by list with user items e.g users=[{'email':'test@test.de']")
            return False

        post_data = {
            "which": "project",
            "entity_id": project_id,
            "users": json.dumps(users),
        }

        return self._get_json_response("/api/v2/remove-users/", postData=post_data)

    """
    Shotgrid API
    """

    def shotgun_get_projects(self, syncsketch_project_id):
        """
        Returns list of Shotgrid projects connected to your account

        :param syncsketch_project_id: <int>
        """
        print("DEPRECATED!  Please use Shotgrid's API")
        print("https://github.com/shotgunsoftware/python-api")

        raise DeprecationWarning("DEPRECATED!  Please use Shotgrid's API.")

    def shotgun_create_config(self, syncsketch_account_id, syncsketch_project_id=None, data=None):
        """
        Create a new Shotgrid configuration for a SyncSketch workspace and optionally a project
        :param int syncsketch_account_id:
        :param int syncsketch_project_id:
        :param dict data: Configuration data.
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

        test_response = self._get_json_response("/api/v2/shotgun/config/test/", postData=test_data, raw_response=True)
        if test_response.status_code == 200:
            return self._get_json_response("/api/v2/shotgun/config/", postData=post_data, raw_response=True)
        else:
            raise Exception("Shotgrid configuration test failed. Please check your Shotgrid config settings.")

    def shotgun_get_playlists(self, syncsketch_account_id, syncsketch_project_id, shotgun_project_id=None):
        """
        Returns list of Shotgrid playlists modified in the last 120 days

        :param int syncsketch_account_id: SyncSketch account id
        :param int syncsketch_project_id: SyncSketch project id
        :param int shotgun_project_id: (optional) Shotgrid project id

        If the syncsketch project is directly linked to a shotgun by the workspace admin, the
        param shotgun_project_id will be ignored and can be omitted during the function call

        """
        url = "/api/v2/shotgun/playlists/{}/".format(syncsketch_account_id)
        if syncsketch_project_id:
            url = self.join_url_path(url, "/{}/".format(syncsketch_project_id))

        data = {"shotgun_project_id": shotgun_project_id}
        return self._get_json_response(url, method="get", getData=data)

    def shotgun_sync_review_notes(self, review_id):
        """
        Sync notes from SyncSketch review to the original shotgun playlist
        Returns task id to use in get_shotgun_sync_review_notes_progress to get progress

        :param review_id: <int>
        :returns <dict>
            message=<STR> "Shotgrid review notes sync started"
            status=<STR> processing/done/failed
            progress_url=<STR> Full url to call for progress/results
            task_id=<STR> task_ids *pass this value to the get_shotgun_sync_review_items_progress function
            percent_complete=<INT> 0-100 value of percent complete
            total_items=<INT> number of items being synced from shotgun
            remaining_items=<INT> number of items not yet pulled from shotgun
        """
        url = "/api/v2/shotgun/sync-review-notes/review/{}/".format(review_id)

        return self._get_json_response(url, method="post")

    def get_shotgun_sync_review_notes_progress(self, task_id):
        """
        Returns status of review notes sync for the task id provided in shotgun_sync_review_notes

        :param task_id: <str/uuid>
        :returns <dict>
            message=<STR> "Shotgrid review notes sync started"
            status=<STR> processing/done/failed
            progress_url=<STR> Full url to call for progress/results
            task_id=<STR> task_ids *pass this value to the get_shotgun_sync_review_items_progress function
            percent_complete=<INT> 0-100 value of percent complete
            total_items=<INT> number of items being synced from shotgun
            remaining_items=<INT> number of items not yet pulled from shotgun
        """
        url = "/api/v2/shotgun/sync-review-notes/{}/".format(task_id)

        return self._get_json_response(url, method="get")

    def shotgun_sync_review_items(self, syncsketch_project_id, playlist_code, playlist_id, review_id=None):
        """
        Create or update SyncSketch review with shotgun playlist items
        Returns task id to use in get_shotgun_sync_review_items_progress to get progress

        :param syncsketch_project_id
        :param playlist_code
        :param playlist_id
        :param review_id (optional)
        :returns <dict>
            message=<STR> "Shotgrid review item sync started",
            status=<STR> processing/done/failed,
            progress_url=<STR> Full url to call for progress/results,
            task_id=<STR> task_ids *pass this value to the get_shotgun_sync_review_items_progress function,
            percent_complete=<INT> 0-100 value of percent complete,
            total_items=<INT> number of items being synced from shotgun,
            remaining_items=<INT> number of items not yet pulled from shotgun,
            data=<dict>
                review_id=<INT> review.id,
                review_link=<STR> url link to the syncsketch player with the review pulled from shotgun,
        )
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

    def get_shotgun_sync_review_items_progress(self, task_id):
        """
        Returns status of review items sync for the task id provided in shotgun_sync_review_items

        :param task_id: <str/uuid>
        :returns <dict>
            message=<STR> "Shotgrid review item sync started",
            status=<STR> processing/done/failed,
            progress_url=<STR> Full url to call for progress/results,
            task_id=<STR> task_ids *pass this value to the get_shotgun_sync_review_items_progress function,
            percent_complete=<INT> 0-100 value of percent complete,
            total_items=<INT> number of items being synced from shotgun,
            remaining_items=<INT> number of items not yet pulled from shotgun,
        )
        """
        print("Deprecated.  Response is printed in the shotgun_sync_review_items() function")

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
    getMediaByReviewId = get_media_by_review_id
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
