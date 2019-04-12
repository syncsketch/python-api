# Syncsketch-API
This package provides method's to communicate with the syncsketch servers and wraps CRUD (create, reade, update, delete) method's to interact with Reviews.

### Getting Started



#### Installation

    pip install git+git:github.com/syncsketch/python-api.git

### Usage:

Interacting with the syncsketch-api is very easy and we provide convenient method's like  `addProject`, `addMedia`, `addReview`. 

### Basic Examples


#### Authentication
Before we can start working, we need to get an `API_KEY` which you can obtain from the syncsketch [settings page](https://syncsketch.com/pro/#userProfile/settingsTab). Follow the given link, login and scroll down to the bottom headline `Developer Options` to see your 40 character API-Key.


Setting up a connection with your syncsketch project's is as easy as following. 

    from syncsketch import SyncSketchAPI
    s = SyncSketchAPI('USERMAIL','API_KEY')]
    s.isConnected()

If you got a `200` as a response, you successfully connected to the syncsketch server! You can proceed with the next examples. We will skip the setup code for the next examples and the snippets will rely on each other, so make sure you run them one by one.






##### 1) Choose your Account

Before we can create/read/update/delete reviews, we need to select an account

    accounts = s.getAccounts()
    firstAccount = accounts['objects'][0]

##### 2) Create A Project

Let's create a project with the selected account

    project = s.addProject(firstAccount.id, 'DEV Example Project', 'DEV API Testing')

This creates a new Project called `Dev Example Project` with the description `DEV API Testing`


##### 3) Create a Review

We can now add a Review to our newly created Project using it's `id`

    review = s.addReview(project['id'],'DEV Review (api)','DEV Syncsketch API Testing')


##### 4) Read Reviews


    print(s.getReviewsByProjectId(project['id'])


##### Upload a review-item

You can upload a file to the created review with the review id.

    itemData = s.addMedia(review['id'],'test.webm')




### Additional Examples

##### Adding a user to the project
    addedUsers = s.addUsers(firstProjectId,[{'email':'test@syncsketch.com','permission':'viewer'}])
    print(addedUser)


##### Traverse all Reviews
    projects = s.getProjects()
    for project in projects['objects']:
        print(project)


## Production Examples


You might wan't to see some minimal examples on how an integration would work with a 3rd party AP. We are providing some examples to get you started.