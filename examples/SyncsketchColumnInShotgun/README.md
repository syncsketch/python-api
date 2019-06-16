### Create a version linked to syncsketch

Note: 

This example creates a version in Shotgun and synchronizes it with syncsketch and adds a column in Shotgun, so you can easily access it. We will skip the shotgun introduction as it is covered very well in the original docs. [Shotgun Tutorial](http://developer.shotgunsoftware.com/python-api/cookbook/tutorials.html#basic)



#### Getting started:
- Make sure you created a Shotgun Userscript ([Howto](http://developer.shotgunsoftware.com/python-api/authentication.html))
- Syncsketch API Code (Howto)
- Check if both packages are installed (Py2):

        pip install git+git://github.com/shotgunsoftware/python-api.git
        pip install git+git:github.com/syncsketch/python-api.git

- Make sure a shotgun demo project exists

#### Create a version linked to a project


Once we have all required point's we can start with our examples



```
import shotgun_api3
from syncsketch import SyncSketchAPI
```

1) Authenticate

```
    ss = SyncSketchAPI('YOURUSERNAME','YOURAPICODE')`
    sg = shotgun_api3.Shotgun("https://yourstudio.shotgunstudio.com/",
                        script_name="sandbox",
                        api_key="SYNCSKETCHAPI")
```

2) Define some static data

You can lookup this data login intoshotgun and adding the `id` column in the views. 

```
    shot_id = 86
    shot_code = 'bbf002'
```