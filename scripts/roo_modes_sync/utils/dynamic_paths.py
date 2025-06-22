#!/usr/bin/env python3
"""
Dynamic path resolution utilities.

This module provides utilities for resolving paths dynamically without hardcoded
usernames or system-specific paths, making scripts portable across different
user environments.
"""

import os
import getpass
from pathlib import Path
from typing import Optional, List


def get_user_home() -> Path:
    """
    Get the user's home directory dynamically.
    
    Returns:
        Path to the user's home directory
    """
    return Path.home()


def get_current_username() -> str:
    """
    Get the current username dynamically.
    
    Returns:
        Current username
    """
    return getpass.getuser()


def get_vscode_config_path(app_name: str = "Code") -> Path:
    """
    Get VSCode/VSCodium config path dynamically.
    
    Args:
        app_name: The application name ("Code" for VSCode, "VSCodium" for VSCodium)
        
    Returns:
        Path to the VSCode/VSCodium configuration directory
    """
    home = get_user_home()
    return home / ".config" / app_name / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings"


def get_custom_modes_path(app_name: str = "Code") -> Path:
    """
    Get custom modes file path dynamically.
    
    Args:
        app_name: The application name ("Code" for VSCode, "VSCodium" for VSCodium)
        
    Returns:
        Path to the custom_modes.yaml file
    """
    return get_vscode_config_path(app_name) / "custom_modes.yaml"


def find_vscode_config_paths() -> List[Path]:
    """
    Find all possible VSCode/VSCodium config paths on the system.
    
    Returns:
        List of possible config paths, ordered by likelihood
    """
    home = get_user_home()
    possible_apps = ["Code", "VSCodium", "code", "code-insiders"]
    
    paths = []
    for app in possible_apps:
        config_path = home / ".config" / app / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings"
        paths.append(config_path)
    
    return paths


def find_existing_custom_modes_file() -> Optional[Path]:
    """
    Find an existing custom_modes.yaml file in any VSCode/VSCodium installation.
    
    Returns:
        Path to an existing custom_modes.yaml file, or None if not found
    """
    for config_path in find_vscode_config_paths():
        custom_modes_file = config_path / "custom_modes.yaml"
        if custom_modes_file.exists():
            return custom_modes_file
    
    return None


def resolve_workspace_path(workspace_hint: Optional[str] = None) -> Path:
    """
    Resolve workspace path dynamically.
    
    Args:
        workspace_hint: Optional hint for workspace location
        
    Returns:
        Resolved workspace path
    """
    if workspace_hint:
        return Path(workspace_hint).resolve()
    
    # Try environment variable
    if "WORKSPACE_PATH" in os.environ:
        return Path(os.environ["WORKSPACE_PATH"]).resolve()
    
    # Try common workspace environment variables
    workspace_vars = ["PWD", "PROJECT_ROOT", "WORKSPACE_FOLDER"]
    for var in workspace_vars:
        if var in os.environ:
            return Path(os.environ[var]).resolve()
    
    # Fall back to current directory
    return Path.cwd().resolve()


def get_project_root_from_script(script_path: Optional[Path] = None) -> Path:
    """
    Get project root directory based on script location.
    
    Args:
        script_path: Path to the script file (defaults to caller's __file__)
        
    Returns:
        Project root directory path
    """
    if script_path is None:
        # This will need to be called with __file__ from the calling script
        raise ValueError("script_path must be provided")
    
    # Assuming scripts are typically in PROJECT_ROOT/scripts/ or deeper
    script_dir = Path(script_path).resolve().parent
    
    # Look for common project root indicators
    current_dir = script_dir
    for _ in range(5):  # Don't go more than 5 levels up
        if any((current_dir / indicator).exists() for indicator in [
            ".git", ".gitignore", "README.md", "pyproject.toml", "setup.py", "package.json"
        ]):
            return current_dir
        
        parent = current_dir.parent
        if parent == current_dir:  # Reached filesystem root
            break
        current_dir = parent
    
    # Fall back to going up from scripts directory
    if "scripts" in script_dir.parts:
        # Find the scripts directory and go one level up
        parts = script_dir.parts
        scripts_index = parts.index("scripts")
        return Path(*parts[:scripts_index])
    
    # Final fallback
    return script_dir.parent


def create_directory_if_not_exists(path: Path) -> bool:
    """
    Create directory and all parent directories if they don't exist.
    
    Args:
        path: Directory path to create
        
    Returns:
        True if directory was created or already exists, False on error
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def resolve_template_path(template_path: str, **kwargs) -> str:
    """
    Resolve template variables in a path string.
    
    Args:
        template_path: Path with template variables like ${HOME}, ${USER}, etc.
        **kwargs: Additional variables to substitute
        
    Returns:
        Resolved path string
    """
    substitutions = {
        'HOME': str(get_user_home()),
        'USER': get_current_username(),
        'USERNAME': get_current_username(),
        **kwargs
    }
    
    result = template_path
    for var, value in substitutions.items():
        result = result.replace(f"${{{var}}}", value)
        result = result.replace(f"${var}", value)
    
    return result