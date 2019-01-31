# -*- coding: utf-8 -*-
# @Author: floepi
# @Date:   2015-06-04 17:42:44
# @Last Modified by:   Philip Floetotto
# @Last Modified time: 2017-05-11 12:21:21
#!/usr/local/bin/python

import pprint

from syncsketch import SyncSketchAPI
s = SyncSketchAPI('YOUR USERNAME','YOUR API KEY')

# Query your account
# accounts = s.getAccounts()
# firstAccount = accounts['objects'][0]

# Create your first project
# newProject = s.addProject(firstAccount.id, 'My First Project', 'Testing the API')
# print newProject

# Get a list of all projects in your account
# projects = s.getProjects()
# for project in projects['objects']:
#     print project

# get reviews in the first project
# firstProjectId = projects['objects'][0]['id']
# print s.getReviewsByProjectId(firstProjectId)

# add a new review to the first project
# addedReview = s.addReview(project['id'],'New Review (api)','Here is a description')
# print addedReview

# upload a file to the review
# itemData = s.addMedia(addedReview['id'],'test.webm')
# print itemData

# Adding a user to the project
# addedUsers = s.addUsers(firstProjectId,[{'email':'test@syncsketch.com','permission':'viewer'}])
# print addedUsers


