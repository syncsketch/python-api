"""Tests that camelCase aliases point to the correct snake_case methods."""

import pytest

from syncsketch import SyncSketchAPI


@pytest.mark.parametrize(
    "alias,target",
    [
        # Core
        ("isConnected", "is_connected"),
        # Accounts
        ("getAccounts", "get_accounts"),
        # Projects
        ("getProjects", "get_projects"),
        ("getProjectsByName", "get_projects_by_name"),
        ("getProjectById", "get_project_by_id"),
        ("addProject", "create_project"),
        ("deleteProject", "delete_project"),
        # Reviews
        ("addReview", "create_review"),
        ("getReviewsByProjectId", "get_reviews_by_project_id"),
        ("getReviewByName", "get_review_by_name"),
        ("getReviewById", "get_review_by_id"),
        ("deleteReview", "delete_review"),
        # Items
        ("getItem", "get_item"),
        ("addItem", "add_item"),
        ("updateItem", "update_item"),
        ("addMedia", "add_media"),
        ("addMediaByURL", "add_media_by_url"),
        ("getMediaByReviewId", "get_items_by_review_id"),
        ("get_media_by_review_id", "get_items_by_review_id"),
        ("getMedia", "get_media"),
        ("connectItemToReview", "connect_item_to_review"),
        ("deleteItem", "delete_item"),
        # v1 alias
        ("add_media_v1", "add_media"),
        # Users
        ("getUsersByName", "get_users_by_name"),
        ("getUsersByProjectId", "get_users_by_project_id"),
        ("getUserById", "get_user_by_id"),
        ("addUsers", "add_users"),
        ("getCurrentUser", "get_current_user"),
        # Annotations
        ("addComment", "add_comment"),
        ("getGreasePencilOverlays", "get_grease_pencil_overlays"),
        ("getAnnotations", "get_annotations"),
        # Tree
        ("getTree", "get_tree"),
        # Shotgrid/Shotgun aliases
        ("get_shotgun_sync_review_items_progress", "get_shotgrid_sync_review_items_progress"),
        ("shotgun_sync_review_items", "shotgrid_sync_review_items"),
        ("get_shotgun_sync_review_notes_progress", "get_shotgrid_sync_review_notes_progress"),
        ("shotgun_sync_new_item_notes", "shotgrid_sync_new_item_notes"),
        ("shotgun_sync_review_notes", "shotgrid_sync_review_notes"),
        ("shotgun_get_playlists", "shotgrid_get_playlists"),
        ("shotgun_create_config", "shotgrid_create_config"),
        ("shotgun_get_projects", "shotgrid_get_projects"),
    ],
)
def test_backward_compat_alias(alias, target):
    assert getattr(SyncSketchAPI, alias) is getattr(SyncSketchAPI, target)
