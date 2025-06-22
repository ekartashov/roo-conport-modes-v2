#!/usr/bin/env python3
"""
Tests for dynamic username path resolution.

This file tests that hardcoded usernames are replaced with dynamic detection
to ensure the CLI works correctly across different user environments.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import getpass

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from cli import get_default_modes_dir, main
except ImportError:
    # Fallback for initial test setup
    def get_default_modes_dir():
        return Path("modes")
    def main():
        return 0


class TestDynamicUsernamePaths:
    """Test suite for dynamic username path resolution."""
    
    def test_no_hardcoded_usernames_in_cli_module(self):
        """
        Test that CLI module does not contain hardcoded usernames.
        """
        cli_file = Path(__file__).parent.parent / "cli.py"
        content = cli_file.read_text()
        
        # Check for common hardcoded username patterns
        hardcoded_patterns = [
            "/home/user/",
            "/home/admin/",
            "/home/developer/",
            "/Users/user/",
            "C:\\Users\\user\\",
            "C:\\Users\\admin\\"
        ]
        
        for pattern in hardcoded_patterns:
            assert pattern not in content, f"Found hardcoded path pattern '{pattern}' in cli.py"
    
    def test_get_user_home_directory_dynamically(self):
        """
        Test that we can get the user's home directory dynamically.
        """
        # This should work on all platforms
        home_dir = Path.home()
        assert home_dir.exists(), f"User home directory should exist: {home_dir}"
        assert home_dir.is_absolute(), f"Home directory should be absolute: {home_dir}"
        
        # Test alternative methods
        home_from_os = Path(os.path.expanduser("~"))
        assert home_from_os == home_dir, "Path.home() and os.path.expanduser('~') should match"
    
    def test_get_current_username_dynamically(self):
        """
        Test that we can get the current username dynamically.
        """
        # Get username through multiple methods
        username_getpass = getpass.getuser()
        username_env = os.environ.get('USER') or os.environ.get('USERNAME')
        
        assert username_getpass, "Should be able to get username via getpass.getuser()"
        assert len(username_getpass) > 0, "Username should not be empty"
        
        # On most systems, these should match (but not required for the test to pass)
        if username_env:
            # Just verify we can get it, don't require they match (some systems differ)
            assert len(username_env) > 0, "Username from environment should not be empty"
    
    def test_build_config_paths_dynamically(self):
        """
        Test that configuration paths can be built dynamically without hardcoded usernames.
        """
        # Test VSCode/VSCodium paths
        home = Path.home()
        
        # Common VSCode config locations
        vscode_configs = [
            home / ".config" / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings",
            home / ".config" / "VSCodium" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings",
        ]
        
        for config_path in vscode_configs:
            # Path should be absolute and under user's home
            assert config_path.is_absolute(), f"Config path should be absolute: {config_path}"
            assert str(config_path).startswith(str(home)), f"Config path should be under user home: {config_path}"
            # We can't assert these exist since they depend on VSCode installation
    
    def test_workspace_paths_without_hardcoded_usernames(self):
        """
        Test that workspace paths can be determined without hardcoded usernames.
        """
        # Current working directory method
        cwd_path = Path.cwd()
        assert cwd_path.is_absolute(), "Current working directory should be absolute"
        
        # Script-relative method (like our current implementation)
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent.parent  # From test dir to project root
        assert project_root.is_absolute(), "Project root should be absolute"
        
        # Environment variable method
        with patch.dict(os.environ, {"PROJECT_ROOT": str(project_root)}):
            env_project_root = Path(os.environ.get("PROJECT_ROOT", "."))
            assert env_project_root.is_absolute(), "Environment-based project root should be absolute"


class TestFixGlobalConfigScript:
    """Test the fix_global_config.py script for hardcoded paths."""
    
    def test_fix_global_config_uses_dynamic_paths(self):
        """
        Test that fix_global_config.py should use dynamic path resolution.
        """
        fix_script_path = Path(__file__).parent.parent.parent / "fix_global_config.py"
        
        if fix_script_path.exists():
            content = fix_script_path.read_text()
            
            # This test will initially fail - that's the point of TDD
            assert "/home/user/" not in content, "fix_global_config.py should not contain hardcoded '/home/user/' paths"
            assert "/home/admin/" not in content, "fix_global_config.py should not contain hardcoded '/home/admin/' paths"
            
            # Should contain dynamic path resolution
            dynamic_indicators = [
                "Path.home()",
                "os.path.expanduser",
                "getpass.getuser()",
                "os.environ.get('USER')",
                "os.environ.get('USERNAME')",
                "from roo_modes_sync.utils.dynamic_paths",  # Our dynamic path utilities
                "find_existing_custom_modes_file",
                "get_custom_modes_path"
            ]
            
            has_dynamic = any(indicator in content for indicator in dynamic_indicators)
            assert has_dynamic, f"fix_global_config.py should use dynamic path resolution methods: {dynamic_indicators}"


class TestUtilitiesAndDocs:
    """Test utilities and documentation files for hardcoded paths."""
    
    def test_utilities_modes_enhancement_uses_dynamic_workspace(self):
        """
        Test that utilities mode enhancement files use dynamic workspace paths.
        """
        enhancement_file = Path(__file__).parent.parent.parent / "utilities" / "modes" / "docs-mode-enhancement.js"
        
        if enhancement_file.exists():
            content = enhancement_file.read_text()
            
            # This test will initially fail - that's the point of TDD
            assert "/home/user/" not in content, "docs-mode-enhancement.js should not contain hardcoded '/home/user/' paths"
            
            # Should use environment variables or dynamic detection
            dynamic_indicators = [
                "process.env.HOME",
                "process.env.USER",
                "process.cwd()",
                "os.homedir()",
                "${workspace"  # Template variable
            ]
            
            has_dynamic = any(indicator in content for indicator in dynamic_indicators)
            assert has_dynamic, f"docs-mode-enhancement.js should use dynamic path resolution: {dynamic_indicators}"
    
    def test_documentation_examples_use_template_paths(self):
        """
        Test that documentation examples use template paths instead of hardcoded ones.
        """
        docs_dir = Path(__file__).parent.parent.parent / "docs" / "examples"
        
        if docs_dir.exists():
            for doc_file in docs_dir.glob("*.js"):
                content = doc_file.read_text()
                
                # Should not contain hardcoded user paths
                assert "/home/user/" not in content, f"{doc_file.name} should not contain hardcoded '/home/user/' paths"
                
                # Should use template variables or placeholders
                if "workspace" in content.lower():
                    template_indicators = [
                        "${workspace}",
                        "[WORKSPACE_PATH]",
                        "/path/to/workspace",
                        "process.env.WORKSPACE",
                        "YOUR_WORKSPACE_PATH"
                    ]
                    
                    has_template = any(indicator in content for indicator in template_indicators)
                    assert has_template, f"{doc_file.name} should use template variables for workspace paths"
    
    def test_specific_documentation_examples_hardcoded_paths(self):
        """
        Test specific documentation examples that are known to have hardcoded paths.
        This test is designed to fail until the examples are fixed.
        """
        example_files = [
            "validation-checkpoints-usage.js",
            "docs-mode-enhancement-usage.js",
            "knowledge-first-guidelines-usage.js"
        ]
        
        docs_dir = Path(__file__).parent.parent.parent.parent / "docs" / "examples"
        hardcoded_files_found = []
        
        for filename in example_files:
            file_path = docs_dir / filename
            if file_path.exists():
                content = file_path.read_text()
                if "/home/user/" in content:
                    hardcoded_files_found.append(filename)
        
        # This should fail until we fix the files
        assert len(hardcoded_files_found) == 0, f"These files contain hardcoded '/home/user/' paths: {hardcoded_files_found}"
    
    def test_troubleshooting_guide_uses_template_paths(self):
        """
        Test that TROUBLESHOOTING.md uses template paths instead of hardcoded usernames.
        """
        troubleshooting_file = Path(__file__).parent.parent.parent / "TROUBLESHOOTING.md"
        
        if troubleshooting_file.exists():
            content = troubleshooting_file.read_text()
            
            # Should use template notation like [YourUsername] instead of specific usernames
            template_indicators = [
                "[YourUsername]",
                "[USERNAME]",
                "${USER}",
                "[USER]",
                "your-username"
            ]
            
            has_template = any(indicator in content for indicator in template_indicators)
            
            # If it mentions home directories, it should use templates
            if "/home/" in content:
                assert has_template, "TROUBLESHOOTING.md should use template variables like [YourUsername] for paths"


class TestDynamicPathUtilities:
    """Test utilities for dynamic path resolution."""
    
    def test_create_dynamic_config_path_function(self):
        """
        Test that we can create a utility function for dynamic config paths.
        """
        # This tests the interface we want to implement
        def get_vscode_config_path(app_name="Code"):
            """Get VSCode/VSCodium config path dynamically."""
            home = Path.home()
            return home / ".config" / app_name / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings"
        
        def get_custom_modes_path(app_name="Code"):
            """Get custom modes file path dynamically."""
            return get_vscode_config_path(app_name) / "custom_modes.yaml"
        
        # Test the functions work
        vscode_path = get_vscode_config_path("Code")
        vscodium_path = get_vscode_config_path("VSCodium")
        
        assert vscode_path != vscodium_path, "Different apps should have different paths"
        assert vscode_path.is_absolute(), "VSCode path should be absolute"
        assert vscodium_path.is_absolute(), "VSCodium path should be absolute"
        
        # Test custom modes paths
        modes_path_vscode = get_custom_modes_path("Code")
        modes_path_vscodium = get_custom_modes_path("VSCodium")
        
        assert modes_path_vscode.name == "custom_modes.yaml", "Should point to custom_modes.yaml"
        assert modes_path_vscodium.name == "custom_modes.yaml", "Should point to custom_modes.yaml"
        assert modes_path_vscode != modes_path_vscodium, "Different apps should have different modes paths"
    
    def test_create_dynamic_workspace_resolver(self):
        """
        Test that we can create a utility for dynamic workspace resolution.
        """
        def resolve_workspace_path(workspace_hint=None):
            """Resolve workspace path dynamically."""
            if workspace_hint:
                return Path(workspace_hint).resolve()
            
            # Try environment variable
            if "WORKSPACE_PATH" in os.environ:
                return Path(os.environ["WORKSPACE_PATH"]).resolve()
            
            # Fall back to current directory
            return Path.cwd().resolve()
        
        # Test with explicit path
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = resolve_workspace_path(temp_dir)
            assert workspace_path == Path(temp_dir).resolve()
        
        # Test with environment variable
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"WORKSPACE_PATH": temp_dir}):
                workspace_path = resolve_workspace_path()
                assert workspace_path == Path(temp_dir).resolve()
        
        # Test fallback to current directory
        with patch.dict(os.environ, {}, clear=True):
            workspace_path = resolve_workspace_path()
            assert workspace_path == Path.cwd().resolve()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])