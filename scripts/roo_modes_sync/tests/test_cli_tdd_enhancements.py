#!/usr/bin/env python3
"""
TDD tests for CLI enhancements: recursive search and optional modes-dir.

This file implements failing tests first (TDD Red phase) for:
1. Making --modes-dir optional with default value "modes" directory
2. Making recursive search the default behavior, add --no-recurse option to disable
3. Ensuring backward compatibility
"""

import pytest
import tempfile
import sys
import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from cli import (
        main, get_default_modes_dir, sync_global, sync_local, list_modes
    )
    from core.discovery import ModeDiscovery
    from core.sync import ModeSync
except ImportError:
    # Fallback: mock for initial test setup
    def main():
        return 0
    def get_default_modes_dir():
        return Path("modes")
    def sync_global(args):
        return 0
    def sync_local(args):
        return 0
    def list_modes(args):
        return 0
    
    class ModeDiscovery:
        def __init__(self, modes_dir, recursive=False):
            self.modes_dir = modes_dir
            self.recursive = recursive
        
        def discover_all_modes(self):
            return {'core': [], 'enhanced': [], 'specialized': [], 'discovered': []}
    
    class ModeSync:
        def __init__(self, modes_dir, recursive=False):
            self.modes_dir = modes_dir
            self.recursive = recursive


class TestCLIRecursiveSearchTDD:
    """TDD tests for recursive search functionality."""
    
    @pytest.fixture
    def temp_project_structure(self):
        """Create a complex project structure for recursive search testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Root modes directory
            modes_dir = project_dir / "modes"
            modes_dir.mkdir()
            
            # Subdirectories with modes
            hybrid_dir = modes_dir / "hybrid"
            hybrid_dir.mkdir()
            
            specialized_dir = modes_dir / "specialized"
            specialized_dir.mkdir()
            
            # Nested subdirectory
            deep_dir = specialized_dir / "deep"
            deep_dir.mkdir()
            
            # Create mode files at different levels
            root_mode = modes_dir / "core.yaml"
            root_mode.write_text("""
slug: core
name: Core Mode
roleDefinition: Core development mode
groups:
  - edit
source: global
""")
            
            hybrid_mode = hybrid_dir / "code-kse-hybrid.yaml"
            hybrid_mode.write_text("""
slug: code-kse-hybrid
name: Code+KSE Hybrid
roleDefinition: Hybrid coding with knowledge synthesis
groups:
  - edit
source: global
""")
            
            specialized_mode = specialized_dir / "conport-maintenance.yaml"
            specialized_mode.write_text("""
slug: conport-maintenance
name: ConPort Maintenance
roleDefinition: ConPort database maintenance
groups:
  - conport
source: global
""")
            
            deep_mode = deep_dir / "deep-analysis.yaml"
            deep_mode.write_text("""
slug: deep-analysis
name: Deep Analysis
roleDefinition: Deep analytical mode
groups:
  - analysis
source: global
""")
            
            yield project_dir
    
    def test_recursive_search_default_behavior_fails_initially(self, temp_project_structure):
        """
        TDD Red: Test that recursive search is NOT currently the default.
        This test should FAIL initially, then pass after implementation.
        """
        modes_dir = temp_project_structure / "modes"
        
        # Test current ModeDiscovery behavior (should be non-recursive by default)
        discovery = ModeDiscovery(modes_dir)
        
        # This assertion should FAIL initially because recursive is not implemented
        # We expect to find only 1 mode (core.yaml) in root, not all 4 modes
        modes = discovery.discover_all_modes()
        total_modes = sum(len(category_modes) for category_modes in modes.values())
        
        # This should FAIL - we currently only find root-level modes
        assert total_modes == 4, f"Expected 4 modes with recursive search, got {total_modes}"
    
    def test_recursive_discovery_constructor_parameter_fails_initially(self, temp_project_structure):
        """
        TDD Red: Test that ModeDiscovery doesn't accept recursive parameter yet.
        This test should FAIL initially.
        """
        modes_dir = temp_project_structure / "modes"
        
        # This should FAIL - recursive parameter doesn't exist yet
        try:
            discovery = ModeDiscovery(modes_dir, recursive=True)
            # If we get here, the parameter was accepted
            assert hasattr(discovery, 'recursive'), "ModeDiscovery should have recursive attribute"
            assert discovery.recursive == True, "recursive should be True when set"
        except TypeError as e:
            # Expected failure - recursive parameter doesn't exist yet
            pytest.fail(f"ModeDiscovery constructor should accept recursive parameter: {e}")
    
    def test_recursive_search_finds_nested_modes_fails_initially(self, temp_project_structure):
        """
        TDD Red: Test that recursive search finds modes in subdirectories.
        This test should FAIL initially.
        """
        modes_dir = temp_project_structure / "modes"
        
        # This should FAIL - recursive functionality doesn't exist yet
        discovery = ModeDiscovery(modes_dir, recursive=True)
        modes = discovery.discover_all_modes()
        
        # Check that we find modes from all directories
        all_mode_slugs = []
        for category_modes in modes.values():
            all_mode_slugs.extend(category_modes)
        
        expected_modes = {"core", "code-kse-hybrid", "conport-maintenance", "deep-analysis"}
        found_modes = set(all_mode_slugs)
        
        assert found_modes == expected_modes, f"Expected {expected_modes}, got {found_modes}"
    
    def test_no_recurse_flag_functionality_fails_initially(self, temp_project_structure, monkeypatch):
        """
        TDD Red: Test that --no-recurse flag disables recursive search.
        This test should FAIL initially.
        """
        modes_dir = temp_project_structure / "modes"
        
        # Test CLI with --no-recurse flag
        test_args = ["cli.py", "list", "--modes-dir", str(modes_dir), "--no-recurse"]
        monkeypatch.setattr(sys, "argv", test_args)
        
        # This should FAIL - --no-recurse option doesn't exist yet
        with patch('cli.list_modes') as mock_list:
            try:
                result = main()
                # Check that mock was called with non-recursive discovery
                mock_list.assert_called_once()
                args = mock_list.call_args[0][0]
                assert hasattr(args, 'no_recurse'), "CLI should have no_recurse option"
                assert args.no_recurse == True, "no_recurse should be True when flag is set"
            except SystemExit:
                # Expected failure - --no-recurse option doesn't exist yet
                pytest.fail("CLI should accept --no-recurse option")


class TestCLIOptionalModesDirTDD:
    """TDD tests for optional --modes-dir functionality."""
    
    def test_modes_dir_optional_with_default_fails_initially(self, monkeypatch):
        """
        TDD Red: Test that --modes-dir is optional with default "modes".
        This test should FAIL initially if the current implementation requires --modes-dir.
        """
        # Test CLI without --modes-dir argument
        test_args = ["cli.py", "list"]
        monkeypatch.setattr(sys, "argv", test_args)
        
        # Mock get_default_modes_dir to return a known path
        default_modes_dir = Path.cwd() / "modes"
        
        with patch('cli.get_default_modes_dir', return_value=default_modes_dir) as mock_default:
            with patch('cli.list_modes') as mock_list:
                try:
                    result = main()
                    # Should succeed without requiring --modes-dir
                    mock_list.assert_called_once()
                    args = mock_list.call_args[0][0]
                    assert args.modes_dir == default_modes_dir, f"Expected {default_modes_dir}, got {args.modes_dir}"
                except SystemExit as e:
                    # If this fails, it means --modes-dir is still required
                    pytest.fail(f"CLI should work without --modes-dir argument: {e}")
    
    def test_default_modes_dir_resolution_fails_initially(self):
        """
        TDD Red: Test that default modes dir resolves to "modes" directory.
        This test might pass currently, but ensures the behavior is correct.
        """
        # Test the current default behavior
        default_dir = get_default_modes_dir()
        
        # Check if it ends with "modes" (allowing for different absolute paths)
        assert default_dir.name == "modes" or str(default_dir).endswith("/modes"), \
            f"Default modes dir should end with 'modes', got {default_dir}"
    
    def test_modes_dir_argument_parsing_backward_compatibility_fails_initially(self, monkeypatch):
        """
        TDD Red: Test that --modes-dir still works when explicitly provided.
        This test ensures backward compatibility.
        """
        custom_modes_dir = Path("/custom/modes/path")
        test_args = ["cli.py", "list", "--modes-dir", str(custom_modes_dir)]
        monkeypatch.setattr(sys, "argv", test_args)
        
        with patch('cli.list_modes') as mock_list:
            try:
                result = main()
                mock_list.assert_called_once()
                args = mock_list.call_args[0][0]
                assert args.modes_dir == custom_modes_dir, \
                    f"Expected {custom_modes_dir}, got {args.modes_dir}"
            except SystemExit as e:
                pytest.fail(f"CLI should accept explicit --modes-dir: {e}")


class TestCLISyncIntegrationTDD:
    """TDD tests for sync command integration with new features."""
    
    @pytest.fixture
    def temp_modes_structure(self):
        """Create a temporary modes structure for sync testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            modes_dir = project_dir / "modes"
            modes_dir.mkdir()
            
            # Create subdirectory with mode
            hybrid_dir = modes_dir / "hybrid"
            hybrid_dir.mkdir()
            
            # Create mode files
            root_mode = modes_dir / "code.yaml"
            root_mode.write_text("""
slug: code
name: Code Mode
roleDefinition: Code development mode
groups:
  - edit
source: global
""")
            
            hybrid_mode = hybrid_dir / "code-hybrid.yaml"
            hybrid_mode.write_text("""
slug: code-hybrid
name: Code Hybrid
roleDefinition: Hybrid coding mode
groups:
  - edit
source: global
""")
            
            yield project_dir
    
    def test_sync_global_uses_recursive_by_default_fails_initially(self, temp_modes_structure, monkeypatch):
        """
        TDD Red: Test that sync-global uses recursive search by default.
        This test should FAIL initially.
        """
        modes_dir = temp_modes_structure / "modes"
        
        test_args = ["cli.py", "sync-global", "--modes-dir", str(modes_dir), "--dry-run"]
        monkeypatch.setattr(sys, "argv", test_args)
        
        # Mock ModeSync to capture how it's instantiated, but let sync_global run
        with patch('cli.ModeSync') as mock_mode_sync:
            # Mock ModeSync to capture recursive parameter
            mock_instance = MagicMock()
            mock_instance.sync_modes.return_value = True
            mock_instance.global_config_path = Path("/test/path")
            mock_mode_sync.return_value = mock_instance
            
            try:
                result = main()
                # Check that ModeSync was created with recursive=True by default
                mock_mode_sync.assert_called_once()
                call_args = mock_mode_sync.call_args
                
                # This should FAIL - recursive parameter doesn't exist yet
                assert 'recursive' in call_args.kwargs, "ModeSync should be called with recursive parameter"
                assert call_args.kwargs['recursive'] == True, "recursive should be True by default"
                
            except Exception as e:
                pytest.fail(f"sync-global should use recursive search by default: {e}")
    
    def test_sync_global_with_no_recurse_flag_fails_initially(self, temp_modes_structure, monkeypatch):
        """
        TDD Red: Test that sync-global respects --no-recurse flag.
        This test should FAIL initially.
        """
        modes_dir = temp_modes_structure / "modes"
        
        test_args = ["cli.py", "sync-global", "--modes-dir", str(modes_dir), "--no-recurse", "--dry-run"]
        monkeypatch.setattr(sys, "argv", test_args)
        
        with patch('cli.sync_global') as mock_sync:
            try:
                result = main()
                mock_sync.assert_called_once()
                args = mock_sync.call_args[0][0]
                
                # This should FAIL - --no-recurse option doesn't exist yet
                assert hasattr(args, 'no_recurse'), "CLI should accept --no-recurse option"
                assert args.no_recurse == True, "no_recurse should be True when flag is set"
                
            except SystemExit:
                pytest.fail("CLI should accept --no-recurse option for sync-global")
    
    def test_sync_local_uses_recursive_by_default_fails_initially(self, temp_modes_structure, monkeypatch):
        """
        TDD Red: Test that sync-local uses recursive search by default.
        This test should FAIL initially.
        """
        modes_dir = temp_modes_structure / "modes"
        
        with tempfile.TemporaryDirectory() as temp_project:
            test_args = ["cli.py", "sync-local", temp_project, "--modes-dir", str(modes_dir), "--dry-run"]
            monkeypatch.setattr(sys, "argv", test_args)
            
            # Mock ModeSync to capture how it's instantiated, but let sync_local run
            with patch('cli.ModeSync') as mock_mode_sync:
                mock_instance = MagicMock()
                mock_instance.sync_modes.return_value = True
                mock_instance.local_config_path = Path("/test/path")
                mock_mode_sync.return_value = mock_instance
                
                try:
                    result = main()
                    # This should FAIL - recursive parameter doesn't exist yet
                    mock_mode_sync.assert_called_once()
                    call_args = mock_mode_sync.call_args
                    assert 'recursive' in call_args.kwargs, "ModeSync should be called with recursive parameter"
                    assert call_args.kwargs['recursive'] == True, "recursive should be True by default"
                    
                except Exception as e:
                    pytest.fail(f"sync-local should use recursive search by default: {e}")


class TestModeDiscoveryRecursiveTDD:
    """TDD tests for ModeDiscovery recursive functionality."""
    
    @pytest.fixture
    def nested_modes_structure(self):
        """Create nested directory structure for discovery testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            modes_dir = Path(temp_dir) / "modes"
            modes_dir.mkdir()
            
            # Create nested structure: modes/category/subcategory/
            core_dir = modes_dir / "core"
            core_dir.mkdir()
            
            hybrid_dir = modes_dir / "hybrid"
            hybrid_dir.mkdir()
            
            specialized_dir = modes_dir / "specialized"
            specialized_dir.mkdir()
            
            deep_specialized = specialized_dir / "deep"
            deep_specialized.mkdir()
            
            # Create modes at different levels
            (modes_dir / "ask.yaml").write_text("slug: ask\nname: Ask\nroleDefinition: Q&A\ngroups: [ask]\n")
            (core_dir / "code.yaml").write_text("slug: code\nname: Code\nroleDefinition: Coding\ngroups: [edit]\n")
            (hybrid_dir / "code-kse.yaml").write_text("slug: code-kse\nname: Code KSE\nroleDefinition: KSE\ngroups: [edit]\n")
            (specialized_dir / "conport.yaml").write_text("slug: conport\nname: ConPort\nroleDefinition: ConPort\ngroups: [conport]\n")
            (deep_specialized / "analyzer.yaml").write_text("slug: analyzer\nname: Analyzer\nroleDefinition: Analysis\ngroups: [analysis]\n")
            
            yield modes_dir
    
    def test_mode_discovery_recursive_parameter_fails_initially(self, nested_modes_structure):
        """
        TDD Red: Test ModeDiscovery constructor accepts recursive parameter.
        This test should FAIL initially.
        """
        # This should FAIL - recursive parameter doesn't exist yet
        try:
            discovery = ModeDiscovery(nested_modes_structure, recursive=True)
            assert hasattr(discovery, 'recursive'), "ModeDiscovery should store recursive parameter"
        except TypeError:
            pytest.fail("ModeDiscovery should accept recursive parameter")
    
    def test_recursive_glob_pattern_fails_initially(self, nested_modes_structure):
        """
        TDD Red: Test that recursive search uses **/*.yaml pattern.
        This test should FAIL initially.
        """
        discovery = ModeDiscovery(nested_modes_structure, recursive=True)
        
        # Test internal method that should use recursive glob
        # This will fail because the method doesn't exist yet
        assert hasattr(discovery, '_get_yaml_files'), "ModeDiscovery should have _get_yaml_files method"
        
        yaml_files = discovery._get_yaml_files()
        
        # Should find all 5 YAML files
        assert len(yaml_files) == 5, f"Expected 5 YAML files with recursive search, got {len(yaml_files)}"
        
        # Check that files from all directories are found
        file_names = {f.name for f in yaml_files}
        expected_files = {"ask.yaml", "code.yaml", "code-kse.yaml", "conport.yaml", "analyzer.yaml"}
        assert file_names == expected_files, f"Expected {expected_files}, got {file_names}"
    
    def test_non_recursive_behavior_preserved_fails_initially(self, nested_modes_structure):
        """
        TDD Red: Test that non-recursive behavior only finds root-level modes.
        This test should FAIL initially if current behavior changes.
        """
        discovery = ModeDiscovery(nested_modes_structure, recursive=False)
        modes = discovery.discover_all_modes()
        
        all_mode_slugs = []
        for category_modes in modes.values():
            all_mode_slugs.extend(category_modes)
        
        # Should only find ask.yaml from root directory
        assert len(all_mode_slugs) == 1, f"Expected 1 mode with non-recursive search, got {len(all_mode_slugs)}"
        assert "ask" in all_mode_slugs, f"Expected 'ask' mode, got {all_mode_slugs}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])