"""
Utilities package for roo_modes_sync.

This package contains utility modules for dynamic path resolution,
cross-platform compatibility, and other common functionality.
"""

from .dynamic_paths import (
    get_user_home,
    get_current_username,
    get_vscode_config_path,
    get_custom_modes_path,
    find_vscode_config_paths,
    find_existing_custom_modes_file,
    resolve_workspace_path,
    get_project_root_from_script,
    create_directory_if_not_exists,
    resolve_template_path
)

__all__ = [
    'get_user_home',
    'get_current_username',
    'get_vscode_config_path',
    'get_custom_modes_path',
    'find_vscode_config_paths',
    'find_existing_custom_modes_file',
    'resolve_workspace_path',
    'get_project_root_from_script',
    'create_directory_if_not_exists',
    'resolve_template_path'
]