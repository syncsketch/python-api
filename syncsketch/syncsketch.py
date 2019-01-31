# -*- coding: utf-8 -*-
"""Summary"""
# @Author: floepi
# @Date:   2015-06-04 17:42:44
# @Last Modified by:   Philip Floetotto
# @Last Modified time: 2018-06-29 11:30:25
#!/usr/local/bin/python

import json
import urllib

import requests


# NOTE - PLEASE INSTALL THE REQUEST MODUL FOR UPLOADING MEDIA
# http://docs.python-requests.org/en/latest/user/install/#install

class SyncSketchAPI:
    """
    Convenience API to communicate with the SyncSketch Service for collaborative online reviews
    """

    def __init__(self,email,api_key,host='https://www.syncsketch.com', useExpiringToken=False, debug = False, apiVersion = 'v1'):
        """Summary
        
        Args:
            email (str): Your email
            api_key (str): Your SyncSketch API Key, found in the settings tab
            host (str, optional): Used for testing or local installs
            useExpiringToken (bool, optional): When using the expiring tokens for authentication.
            Expiring tokens are generated behind a authenticated URL like https://syncsketch.com/users/getToken/
            which returns JSON when the authentication is successful
        """
        # set initial values
        if useExpiringToken:
            self.apiParams = {
                'token': api_key,
                'email': email
            }
        else:
            self.apiParams = {
                'api_key': api_key,
                'username': email
            }

        self.apiVersion = apiVersion
        self.debug = debug
        self.HOST = host
        self.baseURL = self.HOST + '/api/%s/' % self.apiVersion


    def _getJSONResponse(self,entity,getData=False,postData=False,patchData=False):
        url = '%s%s/' % (self.baseURL,entity)
        params = dict(self.apiParams)
        headers={'Content-Type':'application/json'}

        if getData:
            params.update(getData)

        if self.debug:
            print "URL: %s, params: %s" % (url, params)

        if postData:
            r = requests.post(url,params=params,data=json.dumps(postData),headers=headers)
        elif patchData:
            r = requests.patch(url,params=params,data=json.dumps(patchData),headers=headers)
        else:    
            r = requests.get(url,params=params,headers=headers)

        try:
            return r.json()
        except Exception, e:
            if self.debug:
                print e
                print "error %s" % (r.text)

            return {
                'objects':[]
            }

    # Get
    def getTree(self, withItems = False):
        """
            get nested tree of account, projects, reviews and optionally items for the current user
        :param withItems:
        :return:
        """
        getParams = {'fetchItems':1} if withItems else {}
        return self._getJSONResponse('person/tree', getParams)

    def getAccounts(self):
        """Summary

        Returns:
            TYPE: Account
        """
        getParams = {'active':1}
        return self._getJSONResponse('account', getParams)

    def getProjects(self):
        """
        Get a list of currently active projects

        Returns:
            TYPE: Dict with meta information and an array of found projects
        """
        getParams = {'active':1,'account__active':1}
        return self._getJSONResponse('project', getParams)

    def getProjectsByName(self,name):
        """
        Get a project by name regardless of status
        
        Returns:
            TYPE: Dict with meta information and an array of found projects
        """
        getParams = {'name': name}
        return self._getJSONResponse('project',getParams)

    def getProjectById(self,projectId):
        """
        Get single project by id
        :param projectId: Number
        :return:
        """
        return self._getJSONResponse('project/%s' % projectId)

    def getReviewsByProjectId(self,projectId):
        """
        Get list of reviews by project id.
        :param projectId: Number
        :return: Dict with meta information and an array of found projects
        """
        getParams = {'project__id': projectId}
        return self._getJSONResponse('review',getParams)

    def getReviewByName(self,name):
        """
        Get reviews by name using a case insensitive startswith query
        :param name: String - Name of the review
        :return: Dict with meta information and an array of found projects
        """
        getParams = {'name__istartswith': name}
        return self._getJSONResponse('review',getParams)

    def getReviewById(self,reviewId):
        """
        Get single review by id.
        :param reviewId: Number
        :return: Review Dict
        """
        return self._getJSONResponse('review/%s' % reviewId)

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

        return self._getJSONResponse('item', searchCriteria)

    def getMediaByReviewId(self, reviewId):
        """Summary

        Args:
            reviewId (TYPE): Description

        Returns:
            TYPE: Description
        """
        getParams = {'reviews__id': reviewId, 'active': 1}
        return self._getJSONResponse('item', getParams)

    def getAnnotations(self,itemId,revisionId = False):
        """
        Get sketches and comments for an item. Frames have a revision id which signifies a "set of notes".
        When querying an item you'll get the available revisions for this item. If you wish to get only the latest
        revision, please get the revisionId for the latest revision.
        :param itemId: id of the media item you are querying.
        :param (number) revisionId: Optional revisionId to narrow down the results
        :return: dict
        """
        getParams = {'item__id': itemId,'active':1}

        if revisionId:
            getParams['revision__id'] = revisionId

        return self._getJSONResponse('frame',getParams)

    def getUsersByName(self,name):
        getParams = {'name__istartswith': name}
        return self._getJSONResponse('simpleperson',getParams)

    def getUsersByProjectId(self,projectId):
        getParams = {'projects__id': projectId}
        return self._getJSONResponse('simpleperson',getParams)

    def getUserById(self,userId):
        return self._getJSONResponse('simpleperson/%s' % userId)

    def getCurrentUser(self):
        return self._getJSONResponse('simpleperson/currentUser')


    # Add
    def addProject(self, accountId, name, description='', data={}):
        """
        Add a project to your account. Please make sure to pass the accountId which you can query using the getAccounts command.

        :param accountId: Number - id of the account to connect with
        :param name: String
        :param description: String
        :param data: Dict with additional information e.g is_public. Find out more about available fields at /api/v1/project/schema/.
        :return:
        """
        postData = {
            "name":name,
            "description":description,
            "account":'/api/%s/account/%s/' % (self.apiVersion, accountId),
        }
        
        postData.update(data)
        
        return self._getJSONResponse('project',postData=postData)

    def addReview(self,projectId,name, description='',data={}):
        postData = {
            'project': '/api/%s/project/%s/' % (self.apiVersion, projectId),
            'name':name,
            'description':description
        }
        
        postData.update(data)
        
        return self._getJSONResponse('review', postData=postData)

    def addMedia(self, reviewId, filepath, noConvertFlag = False, itemParentId = False):
        """
            Convenience function to upload a file to a review. It will automatically create
            an Item and attach it to the review. NOTE - if you are hosting your own media, please
            use the addItem function and pass in the external_url and external_thumbnail_url
        
        Args:
            reviewId (int): Required reviewId
            filepath (string): path for the file on disk e.g /tmp/movie.webm
            noConvertFlag (bool): the video you are uploading is already in a browser compatible format
            itemParentId (int): set when you want to add a new version of an item. 
                                itemParentId is the id of the item you want to upload a new version for
            
        
        Returns:
            TYPE: Description
        """
        getParams = self.apiParams.copy()

        if noConvertFlag:
            getParams.update({'noConvertFlag':1})

        if itemParentId:
            getParams.update({'itemParentId':itemParentId})

        uploadURL = '%s/items/uploadToReview/%s/?%s' % (self.HOST,reviewId,urllib.urlencode(getParams))

        files = {'reviewFile': open(filepath)}
        r = requests.post(uploadURL, files=files)

        try:
            return json.loads(r.text)
        except Exception:
            print r.text

    def addUsers(self,projectId,users):
        """Summary

        Args:
            projectId (TYPE): Description
            users (TYPE): list with dicts e.g users=[{email:test@test.de,permission:'viewer'}]

        Returns:
            TYPE: Description
        """
        if not isinstance(users,list):
            print "Please add users by list with user items e.g users=[{'email':'test@test.de','permission':'viewer'}]"
            return False

        getParams = {'users': json.dumps(users)}
        return self._getJSONResponse('project/%s/addUsers' % projectId,getParams)

    def addItem(self, reviewId, name, fps, additionalData):
        """
        create a media item record and connect it to a review. This should be used in case you want to add items with externaly hosted
        media by passing in the external_url and external_thumbnail_url to the additionalData dict e.g

        additionalData = {
            fps: 25
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
                duration:3 (in seconds)
                description: the description here
                size: size in byte
                type: image | video
            }

        Returns:
            TYPE: Item
        """



        postData = {
            'reviews': ['/api/%s/review/%s/' % (self.apiVersion, reviewId)],
            'status': 'done',
            'fps': fps,
            'name': name,
        }

        postData.update(additionalData)

        return self._getJSONResponse('item', postData=postData)

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

        itemData = self._getJSONResponse('item/%s' % itemId)

        if itemData['reviews']:
            itemData['reviews'].append('/api/%s/review/%s/' % (self.apiVersion, reviewId))

        patchData = {
            'reviews': itemData['reviews'],
        }

        return self._getJSONResponse('item/%s' % itemId, patchData=patchData)


    # Setting Data
    def updateItem(self,itemId,data):
        """Summary

        Args:
            itemId (TYPE): the id of the item
            data (dict): normal dict with data for item

        Returns:
            TYPE: item
        """
        if not isinstance(data,dict):
            print "Please make sure you pass a dict as data"
            return False

        return self._getJSONResponse('item/%s' % itemId, patchData=data)
    
    # Checking connectivity
    def isConnected(self):
        """
        Convenience function to check if the API is connected to SyncSketch
        Will check against Status Code 200 and return False if not which most likely would be
        and authorization error
        :return:
        """
        url = '%s%s/' % (self.baseURL, 'person/connected')
        params = self.apiParams
        r = requests.get(url, params=params)
        return r.status_code == 200

    def getGreasePencilOverlays(self, reviewId, itemId):
        """Download overlay sketches for Maya Greasepencil.

        Download overlay sketches for Maya Greasepencil. Function will download
        a zip file which contains an XML and the sketches as png files. Maya
        can load the zip file to overlay the sketches over the 3D model!

            For more information visit:
            https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2015/ENU/Maya/files/Grease-Pencil-Tool-htm.html

        :return: filePath to the zip file with the greasePencil data.

        PLEASE make sure that /tmp is writable

        """
        url = '%s/manage/downloadGreasePencilFile/%s/%s/' % (
            self.HOST,
            reviewId,
            itemId,
        )
        r = requests.get(url, params=dict(self.apiParams))

        if r.status_code == 200:
            data = r.json()
            local_filename = '/tmp/%s.zip' % data['fileName']
            r = requests.get(data['s3Path'], stream=True)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            return local_filename
        else:
            return False
