# Syncsketch Python API

This package provides methods to communicate with the syncsketch servers and wraps CRUD (create, read, update, delete) methods to interact with Reviews.

# Overview

SyncSketch is a syncronized visual review tool for the Film/TV/Games industry.

API access requires an enterprise level account.  For help or more info reach out to us.

### Getting Started

#### Compatibility
This library was tested with and confirmed on python versions:
- 2.7.14+
- 3.6
- 3.8

PyPi package

https://pypi.org/project/syncsketch/

#### Installation

Install using `pip`...

    pip install syncsketch

### Data hierarchy

Within SyncSketch there is a basic data hierarchy that makes it easy to manage your resources

- Account (aka Workspace)
- Project
- Review
- ReviewItem (many-to-many connection table)
- Item
- Frame (aka comment or sketch)

Users can be connected to a workspace and/or project, and may have different permissions on each connection.
It's important to know which connections and permissions your api user has to ensure you can build your integration.
You can find these permissions in the website or ask an admin from your project/workspace.

What does this mean?

_These depend on the specific permission level_

- Account/Workspace connection means you can
  - Edit settings on the workspace
  - Invite new workspace level users
  - Manage projects in the account
  - Workspace level users also get all the permissions listed below in projects
- Project connection means you can
  - Edit settings on the project
  - Invite new project level users
  - Manage reviews in the project
  - Manage items in the reviews
  - Manage comments or sketches on items

### Basic Examples

This page includes simple examples to get you started working with our api, but does not show all the methods or parameters that you can use.
We recommend you read the [source code](https://github.com/syncsketch/python-api/blob/master/syncsketch/syncsketch.py) to see all options. 

#### Authentication
Before we can start working, we need to get an `API_KEY` which you can obtain from the syncsketch [settings page](https://syncsketch.com/pro/#/userProfile/settings). Follow the given link, login and scroll down to the bottom headline `Developer Options` to see your 40 character API-Key.


Setting up a connection with your SyncSketch projects is as easy as following. 

    from syncsketch import SyncSketchAPI
    
    username = "username"
    api_key = "api-key-123"
    
    s = SyncSketchAPI(username, api_key)
    
    # Verify your credentials work
    s.is_connected()

    # Display your current user data
    s.get_current_user()

If you got a `200` response, you successfully connected to the syncsketch server! You can proceed with the next examples. We will skip the setup code for the next examples and the snippets will rely on each other, so make sure you run them one by one.


##### 1) Choose your account

Before we can create/read/update/delete projects and/or reviews, we need to select an Account (internal api name for Workspace)

    # Get a list of workspaces your user has access to
    accounts = s.get_accounts()
    first_account = accounts["objects"][0]

IMPORTANT: You may not see anything in the array returned from `s.get_accounts()`.
This means your user is connected directly to the project(s) and not an account.
If so you can skip this and proceed to fetching `s.get_projects()`.

##### 2) Interact with Projects

Projects are nested under an Account/Workspace

    # List projects your user has access to
    s.get_projects()

Let's create a project with the selected account

    project = s.create_project(first_account["id"], 'DEV Example Project', 'DEV API Testing')

This creates a new Project called `Dev Example Project` with the description `DEV API Testing`


##### 3) Create a review

We can now add a Review to our newly created Project using it's `id`

    review = s.create_review(project['id'], 'DEV Review (api)','DEV Syncsketch API Testing')


##### 4) Get list of reviews


    print(s.get_reviews_by_project_id(project['id'])


##### 5) Upload a review item

You can upload a file to the created review with the review id, we provided one example file in this repo under `examples/test.webm` for testing.

    item_data = s.add_media(review['id'],'examples/test.webm')


If all steps were successful, you should see the following in the web-app. 

![alt text](https://github.com/syncsketch/python-api/blob/documentation/examples/resources/exampleResult.jpg?raw=true)

### Additional Examples

##### Adding a user to the project
    addedUsers = s.add_users_to_project(
        project_id,
        [
            {'email': 'test@syncsketch.com', 'permission':'viewer'}
        ],
        "This is a note to include with the welcome email"
    )
    print(addedUsers)


##### Update sort order of items in a review

    response = s.sort_review_items(
        review_id,
        [
            { "id": 111, "sortorder": 0 },
            { "id": 222, "sortorder": 1 },
            { "id": 333, "sortorder": 2 },
        ]
    )
    print(response)
    Out[1] {u'updated_items': 3}


##### Move items from one review to another

    response = s.move_items(
        new_review_id,
        [
            {
                "review_id": old_review_id,
                "item_id": item_id,
            }
        ]
    )


##### Traverse all Reviews
    projects = s.get_projects()
    
    for project in projects['objects']:
        print(project)


##### Traverse all Accounts 
The fastest way to traverse all Accounts, Projects Reviews, and Items is to get the entire tree

    tree_data = s.get_tree(withItems = True)
    
    for account in tree_data:
        for project in account['projects']:
            if project['active'] == 1:
                print project['name']
                for review in project['reviews']:
                    for item in review['items']:
                        mediaid = item['id']
                        medianame = item['name']
                        print '\t %s:\t%s'%(mediaid, medianame)
