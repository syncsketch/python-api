# -*- coding: utf-8 -*-
"""Summary"""
# @Author: floepi
# @Date:   2015-06-04 17:42:44
# @Last Modified by:   yafes
# @Last Modified time: 2019-03-01 01:59:05
#!/usr/local/bin/python

from __future__ import print_function

import os
import json
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
        self, auth, api_key, host="https://www.syncsketch.com", useExpiringToken=False, debug=False, api_version="v1", use_header_auth=False
    ):
        """Summary

        Args:
            user_auth (str): Your email or username
            api_key (str): Your SyncSketch API Key, found in the settings tab
            host (str, optional): Used for testing or local installs
            useExpiringToken (bool, optional): When using the expiring tokens for authentication.
            Expiring tokens are generated behind a authenticated URL like https://syncsketch.com/users/getToken/
            which returns JSON when the authentication is successful
        """
        # set initial values
        self.user_auth = auth
        self.api_key = api_key
        self.apiParams = dict()
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
            self.apiParams = {"token": self.api_key, "email": self.user_auth}
        else:
            self.apiParams = {"api_key": self.api_key, "username": self.user_auth}

        self.api_version = api_version
        self.debug = debug
        self.HOST = host

    def get_api_base_url(self, api_version=None):
        return self.HOST + "/api/{}/".format(api_version or self.api_version)

    def _getJSONResponse(
        self,
        url,
        method=None,
        getData=None,
        postData=None,
        patchData=None,
        api_version=None,
        content_type="application/json",
        raw_response=False
    ):
        url = self.get_api_base_url(api_version) + url + "/"
        params = dict(self.apiParams)

        # Update headers with custom content-type
        headers = self.headers.copy()
        headers["Content-Type"] = content_type

        if getData:
            params.update(getData)

        if self.debug:
            print("URL: %s, params: %s" % (url, params))

        if postData or method == "post":
            r = requests.post(url, params=params, data=json.dumps(postData), headers=headers)
        elif patchData or method == "patch":
            r = requests.patch(url, params=params, data=json.dumps(patchData), headers=headers)
        else:
            r = requests.get(url, params=params, headers=headers)

        if raw_response:
            # Return the whole response object, not {"objects": []}
            return r

        try:
            return r.json()
        except Exception as e:
            if self.debug:
                print(e)
                print("error %s" % (r.text))

            return {"objects": []}

    # Get
    def getTree(self, withItems=False):
        """
            get nested tree of account, projects, reviews and optionally items for the current user
        :param withItems:
        :return:
        """
        getParams = {"fetchItems": 1} if withItems else {}
        return self._getJSONResponse("person/tree", getData=getParams)

    def getAccounts(self):
        """Summary

        Returns:
            TYPE: Account
        """
        getParams = {"active": 1}
        return self._getJSONResponse("account", getData=getParams)

    def getProjects(self, include_deleted=False, include_archived=False):
        """
        Get a list of currently active projects

        :param include_deleted: boolean: if true, include deleted projects
        :param include_archived: boolean: if true, include archived projects

        Returns:
            TYPE: Dict with meta information and an array of found projects
        """
        getParams = {"active": 1, "is_archived": 0, "account__active": 1}

        if include_deleted:
            del getParams["active"]

        if include_archived:
            del getParams["active"]
            del getParams["is_archived"]

        return self._getJSONResponse("project", getData=getParams)

    def getProjectsByName(self, name):
        """
        Get a project by name regardless of status

        Returns:
            TYPE: Dict with meta information and an array of found projects
        """
        getParams = {"name": name}
        return self._getJSONResponse("project", getData=getParams)

    def getProjectById(self, projectId):
        """
        Get single project by id
        :param projectId: Number
        :return:
        """
        return self._getJSONResponse("project/%s" % projectId)

    def getReviewsByProjectId(self, projectId):
        """
        Get list of reviews by project id.
        :param projectId: Number
        :return: Dict with meta information and an array of found projects
        """
        getParams = {"project__id": projectId, "project__active": 1, "project__is_archived": 0}
        return self._getJSONResponse("review", getData=getParams)

    def getReviewByName(self, name):
        """
        Get reviews by name using a case insensitive startswith query
        :param name: String - Name of the review
        :return: Dict with meta information and an array of found projects
        """
        getParams = {"name__istartswith": name}
        return self._getJSONResponse("review", getData=getParams)

    def getReviewById(self, reviewId):
        """
        Get single review by id.
        :param reviewId: Number
        :return: Review Dict
        """
        return self._getJSONResponse("review/%s" % reviewId)

    def getMedia(self, searchCriteria):
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

        return self._getJSONResponse("item", getData=searchCriteria)

    def getMediaByReviewId(self, reviewId):
        """Summary

        Args:
            reviewId (TYPE): Description

        Returns:
            TYPE: Description
        """
        getParams = {"reviews__id": reviewId, "active": 1}
        return self._getJSONResponse("item", getData=getParams)

    def getAnnotations(self, itemId, revisionId=False):
        """
        Get sketches and comments for an item. Frames have a revision id which signifies a "set of notes".
        When querying an item you'll get the available revisions for this item. If you wish to get only the latest
        revision, please get the revisionId for the latest revision.
        :param itemId: id of the media item you are querying.
        :param (number) revisionId: Optional revisionId to narrow down the results
        :return: dict
        """
        getParams = {"item__id": itemId, "active": 1}

        if revisionId:
            getParams["revision__id"] = revisionId

        return self._getJSONResponse("frame", getData=getParams)

    def getUsersByName(self, name):
        # Uses a custom filter on SimplePersonResource
        getParams = {"name": name}
        return self._getJSONResponse("simpleperson", getData=getParams)

    def getUsersByProjectId(self, project_id):
        # Uses a custom filter on SimplePersonResource
        getParams = {"project_id": project_id}
        return self._getJSONResponse("simpleperson", getData=getParams)

    def getUserById(self, userId):
        return self._getJSONResponse("simpleperson/%s" % userId)

    def getCurrentUser(self):
        return self._getJSONResponse("simpleperson/currentUser")

    # Add
    def addProject(self, accountId, name, description="", data={}):
        """
        Add a project to your account. Please make sure to pass the accountId which you can query using the getAccounts command.

        :param accountId: Number - id of the account to connect with
        :param name: String
        :param description: String
        :param data: Dict with additional information e.g is_public. Find out more about available fields at /api/v1/project/schema/.
        :return:
        """
        postData = {
            "name": name,
            "description": description,
            "account": "/api/%s/account/%s/" % (self.api_version, accountId),
        }

        postData.update(data)

        return self._getJSONResponse("project", postData=postData)

    def addReview(self, projectId, name, description="", data={}):
        postData = {
            "project": "/api/%s/project/%s/" % (self.api_version, projectId),
            "name": name,
            "description": description,
        }

        postData.update(data)

        return self._getJSONResponse("review", postData=postData)

    def addMedia(self, review_id, filepath, artist_name="", noConvertFlag=False, itemParentId=False):
        """
            Convenience function to upload a file to a review. It will automatically create
            an Item and attach it to the review. NOTE - if you are hosting your own media, please
            use the addItem function and pass in the external_url and external_thumbnail_url

        Args:
            review_id (int): Required review_id
            filepath (string): path for the file on disk e.g /tmp/movie.webm
            artist_name (string): The name of the artist you want associated with this media file
            noConvertFlag (bool): the video you are uploading is already in a browser compatible format
            itemParentId (int): set when you want to add a new version of an item.
                                itemParentId is the id of the item you want to upload a new version for

        Returns:
            TYPE: Description
        """
        getParams = self.apiParams.copy()

        if noConvertFlag:
            getParams.update({"noConvertFlag": 1})

        if itemParentId:
            getParams.update({"itemParentId": itemParentId})

        uploadURL = "%s/items/uploadToReview/%s/?%s" % (self.HOST, review_id, urlencode(getParams))

        files = {"reviewFile": open(filepath, "rb")}
        r = requests.post(uploadURL, files=files, data=dict(artist=artist_name), headers=self.headers)

        try:
            return json.loads(r.text)
        except Exception:
            print(r.text)

    def addMediaByURL(self, reviewId, mediaURL, artist_name="", noConvertFlag=False):
        """
            Convenience function to upload a mediaURl to a review. Please use this function when you already have your files in the cloud, e.g
            AWS, Dropbox, Shotgun, etc...

            We will automatically create an Item and attach it to the review.

        Args:
            reviewId (int): Required reviewId
            mediaURL (string): url to the media you are trying to upload
            noConvertFlag (bool): the video you are uploading is already in a browser compatible format and does not need to be converted

        Returns:
            TYPE: Description
        """
        getParams = self.apiParams.copy()

        if not reviewId or not mediaURL:
            raise Exception("You need to pass a review id and a mediaURL")

        if noConvertFlag:
            getParams.update({"noConvertFlag": 1})

        uploadURL = "%s/items/uploadToReview/%s/?%s" % (self.HOST, reviewId, urlencode(getParams))

        r = requests.post(uploadURL, {"mediaURL": mediaURL, "artist": artist_name}, headers=self.headers)

        try:
            return json.loads(r.text)
        except Exception:
            print(r.text)

    def addUsers(self, projectId, users):
        """Summary

        Args:
            projectId (TYPE): Description
            users (TYPE): list with dicts e.g users=[{email:test@test.de,permission:'viewer'}]

        Returns:
            TYPE: Description
        """
        if not isinstance(users, list):
            print(
                "Please add users by list with user items e.g users=[{'email':'test@test.de','permission':'viewer'}]"
            )
            return False

        getParams = {"users": json.dumps(users)}
        return self._getJSONResponse("project/%s/addUsers" % projectId, getData=getParams)

    def addItem(self, reviewId, name, fps, additionalData):
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
            reviewId (TYPE): Required reviewId
            name (TYPE): Name of the item
            fps (TYPE): The frame per second is very important for syncsketch to determine the correct number of frames
            additionalData (TYPE): dictionary with item info like {
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
            "reviews": ["/api/%s/review/%s/" % (self.api_version, reviewId)],
            "status": "done",
            "fps": fps,
            "name": name,
        }

        postData.update(additionalData)

        return self._getJSONResponse("item", postData=postData)

    def connectItemToReview(self, itemId, reviewId):
        """
        adding an existing item record in the database to an existing review by id. This function is useful when
        you don't want to upload an item multiple times but use it in multiple reviews e.g for context.

        Args:
            reviewId (Number): Required reviewId
            itemId (Number): id of the item

        Returns:
            TYPE: Item
        """

        itemData = self._getJSONResponse("item/%s" % itemId)

        if itemData["reviews"]:
            itemData["reviews"].append("/api/%s/review/%s/" % (self.api_version, reviewId))

        patchData = {"reviews": itemData["reviews"]}

        return self._getJSONResponse("item/%s" % itemId, patchData=patchData)

    # Setting Data
    def updateItem(self, itemId, data):
        """Summary

        Args:
            itemId (TYPE): the id of the item
            data (dict): normal dict with data for item

        Returns:
            TYPE: item
        """
        if not isinstance(data, dict):
            print("Please make sure you pass a dict as data")
            return False

        return self._getJSONResponse("item/%s" % itemId, patchData=data)

    # Checking connectivity
    def isConnected(self):
        """
        Convenience function to check if the API is connected to SyncSketch
        Will check against Status Code 200 and return False if not which most likely would be
        and authorization error
        :return:
        """
        url = "person/connected"
        params = self.apiParams

        if self.debug:
            print("URL: %s, params: %s" % (url, params))

        r = self._getJSONResponse(url, raw_response=True)
        return r.status_code == 200

    def getGreasePencilOverlays(self, reviewId, itemId, homedir=None):
        """Download overlay sketches for Maya Greasepencil.

        Download overlay sketches for Maya Greasepencil. Function will download
        a zip file which contains an XML and the sketches as png files. Maya
        can load the zip file to overlay the sketches over the 3D model!

            For more information visit:
            https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2015/ENU/Maya/files/Grease-Pencil-Tool-htm.html

        :return: filePath to the zip file with the greasePencil data.

        PLEASE make sure that /tmp is writable

        """
        url = "%s/manage/downloadGreasePencilFile/%s/%s/" % (self.HOST, reviewId, itemId)
        r = requests.get(url, params=dict(self.apiParams), headers=self.headers)

        if r.status_code == 200:
            data = r.json()
            local_filename = "/tmp/%s.zip" % data["fileName"]
            if homedir:
                local_filename = os.path.join(homedir, "{}.zip".format(data["fileName"]))
            r = requests.get(data["s3Path"], stream=True)
            with open(local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            return local_filename
        else:
            return False

    def shotgun_get_projects(self, syncsketch_project_id):
        """
        Returns list of Shotgun projects connected to your account

        :param syncsketch_project_id: <int>
        """
        url = "shotgun/projects/{}".format(syncsketch_project_id)

        return self._getJSONResponse(url, method="get", api_version="v2")

    def shotgun_get_playlists(self, syncsketch_project_id, shotgun_project_id):
        """
        Returns list of Shotgun playlists modified in the last 120 days

        :param syncsketch_project_id: <int>
        :param shotgun_project_id: <int>
        """
        url = "shotgun/playlists/{}".format(syncsketch_project_id)

        data = {
            "shotgun_project_id": shotgun_project_id
        }
        return self._getJSONResponse(url, method="get", getData=data, api_version="v2")

    def shotgun_sync_review_notes(self, review_id):
        """
        Sync notes from SyncSketch review to the original shotgun playlist
        Returns task id to use in get_shotgun_sync_review_notes_progress to get progress

        :param review_id: <int>
        :returns <dict>
            message=<STR> "Shotgun review notes sync started"
            status=<STR> processing/done/failed
            progress_url=<STR> Full url to call for progress/results
            task_id=<STR> task_ids *pass this value to the get_shotgun_sync_review_items_progress function
            percent_complete=<INT> 0-100 value of percent complete
            total_items=<INT> number of items being synced from shotgun
            remaining_items=<INT> number of items not yet pulled from shotgun
        """
        url = "shotgun/sync-review-notes/review/{}".format(review_id)

        return self._getJSONResponse(url, method="post", api_version="v2")

    def get_shotgun_sync_review_notes_progress(self, task_id):
        """
        Returns status of review notes sync for the task id provided in shotgun_sync_review_notes

        :param task_id: <str/uuid>
        :returns <dict>
            message=<STR> "Shotgun review notes sync started"
            status=<STR> processing/done/failed
            progress_url=<STR> Full url to call for progress/results
            task_id=<STR> task_ids *pass this value to the get_shotgun_sync_review_items_progress function
            percent_complete=<INT> 0-100 value of percent complete
            total_items=<INT> number of items being synced from shotgun
            remaining_items=<INT> number of items not yet pulled from shotgun
        """
        url = "shotgun/sync-review-notes/{}".format(task_id)

        return self._getJSONResponse(url, method="get", api_version="v2")

    def shotgun_sync_review_items(self, syncsketch_project_id, playlist_code, playlist_id, review_id=None):
        """
        Create or update SyncSketch review with shotgun playlist items
        Returns task id to use in get_shotgun_sync_review_items_progress to get progress

        :param syncsketch_project_id
        :param playlist_code
        :param playlist_id
        :param review_id (optional)
        :returns <dict>
            message=<STR> "Shotgun review item sync started",
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
        url = "shotgun/sync-review-items/project/{}".format(syncsketch_project_id)
        if review_id:
            url += "/review/{}".format(review_id)

        data = {
            "playlist_code": playlist_code,
            "playlist_id": playlist_id
        }

        return self._getJSONResponse(url, method="post", postData=data, api_version="v2")

    def get_shotgun_sync_review_items_progress(self, task_id):
        """
        Returns status of review items sync for the task id provided in shotgun_sync_review_items

        :param task_id: <str/uuid>
        :returns <dict>
            message=<STR> "Shotgun review item sync started",
            status=<STR> processing/done/failed,
            progress_url=<STR> Full url to call for progress/results,
            task_id=<STR> task_ids *pass this value to the get_shotgun_sync_review_items_progress function,
            percent_complete=<INT> 0-100 value of percent complete,
            total_items=<INT> number of items being synced from shotgun,
            remaining_items=<INT> number of items not yet pulled from shotgun,
        )
        """
        url = "shotgun/sync-review-items/{}".format(task_id)

        return self._getJSONResponse(url, method="get", api_version="v2")
