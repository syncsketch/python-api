Main Python API for SyncSketch based on the Rest API

Simple Usage example:


```
from syncsketch import SyncSketchAPI
s=SyncSketchAPI('USERNAME','API_KEY', debug=True)

# get accounts
accounts = s.getAccounts()
firstAccount = accounts['objects'][0]

# get projects
projects = s.getProjects()
```