.. SyncSketch Python API Library documentation master file, created by
   sphinx-quickstart on Thu Jul 25 15:46:05 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SyncSketch Python API Library documentation
===========================================

autodoc_member_order = 'bysource'

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. class:: syncsketch.SyncSketchAPI
   :no-index:

   SyncSketchAPI is a class that provides a set of methods to interact with SyncSketch API.

   .. method:: __init__(
         auth,
        api_key,
        host="https://www.syncsketch.com",
        useExpiringToken=False,
        debug=False,
        api_version="v1",
        use_header_auth=False
      )

      Constructor for SyncSketchAPI class.

      :param str auth: The username of the user.
      :param str api_key: The api key of the user.
      :param str host: The host of the SyncSketch API.
      :param bool useExpiringToken: If True, the token will expire after 1 hour.
      :param bool debug: If True, the debug mode will be enabled.
      :param str api_version: The version of the SyncSketch API.
      :param bool use_header_auth: If True, the authentication will be done using headers.
      :return: SyncSketchAPI object.
      :rtype: obj

.. autoclass:: syncsketch.SyncSketchAPI
   :show-inheritance:
   :members:
   :exclude-members: isConnected,get_api_base_url,get_media_by_review_id,join_url_path,addComment,addItem,addMedia,addMediaByURL,addProject,addReview,addUsers,getProjectById,getProjects,getProjectsByName,get_shotgun_sync_review_notes_progress,updateItem,connectItemToReview,deleteItem,deleteProject,deleteReview,getAccounts,getAnnotations,getCurrentUser,getGreasePencilOverlays,getItem,getMedia,add_users,shotgrid_get_projects,getMediaByReviewId,getReviewById,getReviewByName,getReviewsByProjectId,getTree,getUserById,getUsersByName,getUsersByProjectId
   :member-order: bysource
