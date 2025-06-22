"""Test cases for mode synchronization functionality."""

import os
import yaml
import shutil
import pytest
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock

from roo_modes_sync.core.sync import ModeSync
from roo_modes_sync.exceptions import SyncError, ConfigurationError


class TestModeSync:
    """Test cases for ModeSync class."""
    
    @pytest.fixture
    def temp_modes_dir(self, tmp_path):
        """Create a temporary directory for test mode files."""
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        return modes_dir
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create a temporary directory for config files."""
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
        
    @pytest.fixture
    def temp_project_dir(self, tmp_path):
        """Create a temporary directory simulating a project."""
        project_dir = tmp_path / "project"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
    
    @pytest.fixture
    def sync_manager(self, temp_modes_dir):
        """Create a ModeSync instance with temporary directory."""
        sync = ModeSync(temp_modes_dir)
        return sync
    
    def create_mode_file(self, modes_dir: Path, slug: str, config: Dict[str, Any]) -> Path:
        """Helper to create a mode file in the test directory."""
        mode_file = modes_dir / f"{slug}.yaml"
        with open(mode_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return mode_file
    
    def create_valid_mode_config(self, slug: str) -> Dict[str, Any]:
        """Helper to create a valid mode configuration."""
        return {
            'slug': slug,
            'name': f'{slug.title()} Mode',
            'roleDefinition': f'Test {slug} role definition',
            'groups': ['read', 'edit']
        }
    
    def test_init(self, temp_modes_dir):
        """Test ModeSync initialization."""
        sync = ModeSync(temp_modes_dir)
        assert sync.modes_dir == temp_modes_dir
        assert hasattr(sync, 'validator')
        assert hasattr(sync, 'discovery')
    
    def test_set_global_config_path(self, sync_manager, temp_config_dir):
        """Test setting the global config path."""
        config_path = temp_config_dir / "custom_modes.yaml"
        sync_manager.set_global_config_path(config_path)
        assert sync_manager.global_config_path == config_path
        assert sync_manager.local_config_path is None
        
    def test_set_global_config_path_default(self, sync_manager):
        """Test setting the global config path to default."""
        sync_manager.set_global_config_path()
        assert sync_manager.global_config_path == ModeSync.DEFAULT_GLOBAL_CONFIG_PATH
        assert sync_manager.local_config_path is None
        
    def test_set_local_config_path(self, sync_manager, temp_project_dir):
        """Test setting the local config path."""
        sync_manager.set_local_config_path(temp_project_dir)
        assert sync_manager.local_config_path == temp_project_dir / ModeSync.LOCAL_CONFIG_DIR / ModeSync.LOCAL_CONFIG_FILE
        assert sync_manager.global_config_path is None
    
    def test_load_mode_config_valid(self, sync_manager, temp_modes_dir):
        """Test loading a valid mode configuration."""
        slug = 'test-mode'
        config = self.create_valid_mode_config(slug)
        self.create_mode_file(temp_modes_dir, slug, config)
        
        loaded_config = sync_manager.load_mode_config(slug)
        
        assert loaded_config is not None
        assert loaded_config['slug'] == slug
        assert loaded_config['source'] == 'global'
    
    def test_load_mode_config_nonexistent(self, sync_manager):
        """Test loading a nonexistent mode configuration."""
        with pytest.raises(SyncError):
            sync_manager.load_mode_config('nonexistent-mode')
    
    def test_load_mode_config_invalid(self, sync_manager, temp_modes_dir):
        """Test loading an invalid mode configuration."""
        # Create mode with missing required fields
        slug = 'invalid-mode'
        invalid_config = {'slug': slug, 'name': 'Invalid Mode'}
        self.create_mode_file(temp_modes_dir, slug, invalid_config)
        
        with pytest.raises(SyncError):
            sync_manager.load_mode_config(slug)
    
    def test_create_global_config_strategic(self, sync_manager, temp_modes_dir):
        """Test creating global config with strategic ordering."""
        # Create multiple modes of different categories
        core_modes = ['code', 'architect']
        enhanced_modes = ['code-enhanced']
        specialized_modes = ['prompt-enhancer']
        discovered_modes = ['custom-mode']
        
        all_modes = core_modes + enhanced_modes + specialized_modes + discovered_modes
        
        for mode in all_modes:
            self.create_mode_file(
                temp_modes_dir, 
                mode, 
                self.create_valid_mode_config(mode)
            )
        
        config = sync_manager.create_global_config(strategy_name='strategic')
        
        assert 'customModes' in config
        assert len(config['customModes']) == len(all_modes)
        
        # Strategic order should place core modes first
        assert config['customModes'][0]['slug'] in core_modes
        assert config['customModes'][1]['slug'] in core_modes
    
    def test_create_global_config_alphabetical(self, sync_manager, temp_modes_dir):
        """Test creating global config with alphabetical ordering."""
        modes = ['zebra-mode', 'alpha-mode', 'beta-mode']
        
        for mode in modes:
            self.create_mode_file(
                temp_modes_dir, 
                mode, 
                self.create_valid_mode_config(mode)
            )
        
        config = sync_manager.create_global_config(strategy_name='alphabetical')
        
        assert 'customModes' in config
        
        # Alphabetical order should sort alphabetically within categories
        slugs = [mode['slug'] for mode in config['customModes']]
        assert slugs == ['alpha-mode', 'beta-mode', 'zebra-mode']
    
    def test_create_global_config_with_exclusions(self, sync_manager, temp_modes_dir):
        """Test creating global config with mode exclusions."""
        modes = ['mode1', 'mode2', 'mode3']
        
        for mode in modes:
            self.create_mode_file(
                temp_modes_dir, 
                mode, 
                self.create_valid_mode_config(mode)
            )
        
        options = {'exclude': ['mode2']}
        config = sync_manager.create_global_config(options=options)
        
        assert 'customModes' in config
        slugs = [mode['slug'] for mode in config['customModes']]
        assert 'mode1' in slugs
        assert 'mode2' not in slugs
        assert 'mode3' in slugs
    
    def test_create_global_config_with_priority(self, sync_manager, temp_modes_dir):
        """Test creating global config with priority modes."""
        modes = ['mode1', 'mode2', 'mode3']
        
        for mode in modes:
            self.create_mode_file(
                temp_modes_dir, 
                mode, 
                self.create_valid_mode_config(mode)
            )
        
        options = {'priority_first': ['mode3', 'mode1']}
        config = sync_manager.create_global_config(options=options)
        
        assert 'customModes' in config
        slugs = [mode['slug'] for mode in config['customModes']]
        
        # mode3 and mode1 should be first in the specified order
        assert slugs[0] == 'mode3'
        assert slugs[1] == 'mode1'
    
    def test_yaml_formatting_with_custom_dumper(self, sync_manager):
        """Test YAML formatting with custom dumper for proper indentation."""
        import yaml
        from roo_modes_sync.core.sync import CustomYAMLDumper
        
        # Test data structure similar to what we generate
        test_config = {
            'customModes': [
                {
                    'slug': 'test-mode',
                    'name': 'Test Mode',
                    'roleDefinition': 'This is a single line.',
                    'groups': ['read', 'edit'],
                    'source': 'global'
                },
                {
                    'slug': 'multiline-mode',
                    'name': 'Multiline Mode',
                    'roleDefinition': 'This is a\nmultiline string\nwith several lines.',
                    'groups': ['read'],
                    'source': 'global'
                }
            ]
        }
        
        # Test that YAML dumps without errors using our custom dumper
        yaml_output = yaml.dump(test_config, Dumper=CustomYAMLDumper,
                               default_flow_style=False, allow_unicode=True,
                               sort_keys=False, width=float('inf'), indent=2)
        
        # Verify basic structure is preserved
        assert 'customModes:' in yaml_output
        assert 'slug: test-mode' in yaml_output
        assert 'slug: multiline-mode' in yaml_output
        
        # Verify multiline content is properly escaped/formatted
        assert 'This is a' in yaml_output
    
    def test_backup_existing_config(self, sync_manager, temp_config_dir):
        """Test backup of existing global config."""
        config_path = temp_config_dir / "custom_modes.yaml"
        with open(config_path, 'w') as f:
            f.write("customModes: []\n")
            
        sync_manager.set_global_config_path(config_path)
        
        success = sync_manager.backup_existing_config()
        assert success is True
        
        backup_path = config_path.with_suffix('.yaml.backup')
        assert backup_path.exists()
    
    def test_write_global_config(self, sync_manager, temp_config_dir):
        """Test writing global config to file."""
        config_path = temp_config_dir / "custom_modes.yaml"
        sync_manager.set_global_config_path(config_path)
        
        config = {
            'customModes': [
                {
                    'slug': 'test-mode',
                    'name': 'Test Mode',
                    'roleDefinition': 'Test role definition',
                    'groups': ['read'],
                    'source': 'global'
                }
            ]
        }
        
        success = sync_manager.write_global_config(config)
        assert success is True
        assert config_path.exists()
        
        # Verify content was written correctly
        with open(config_path, 'r') as f:
            content = f.read()
            assert 'customModes:' in content
            assert 'slug: test-mode' in content
    
    def test_sync_modes(self, sync_manager, temp_modes_dir, temp_config_dir):
        """Test full sync process."""
        config_path = temp_config_dir / "custom_modes.yaml"
        sync_manager.set_global_config_path(config_path)
        
        # Create a few test modes
        modes = ['code', 'debug', 'custom-mode']
        for mode in modes:
            self.create_mode_file(
                temp_modes_dir, 
                mode, 
                self.create_valid_mode_config(mode)
            )
        
        # Run sync with dry_run first
        success = sync_manager.sync_modes(dry_run=True)
        assert success is True
        assert not config_path.exists()  # Should not create file in dry run
        
        # Run actual sync
        success = sync_manager.sync_modes()
        assert success is True
        assert config_path.exists()
        
        # Verify content
        with open(config_path, 'r') as f:
            content = f.read()
            for mode in modes:
                assert f'slug: {mode}' in content
    
    def test_sync_modes_with_no_valid_modes(self, sync_manager, temp_modes_dir, temp_config_dir):
        """Test sync process with no valid modes."""
        config_path = temp_config_dir / "custom_modes.yaml"
        sync_manager.set_global_config_path(config_path)
        
        # Create invalid mode
        invalid_config = {'slug': 'invalid', 'name': 'Invalid Mode'}
        self.create_mode_file(temp_modes_dir, 'invalid', invalid_config)
        
        success = sync_manager.sync_modes()
        assert success is False
        
    def test_create_local_mode_directory(self, sync_manager, temp_project_dir):
        """Test creating local mode directory structure."""
        # Setup
        sync_manager.set_local_config_path(temp_project_dir)
        
        # Test
        created = sync_manager.create_local_mode_directory()
        
        # Verify
        assert created is True
        assert (temp_project_dir / ModeSync.LOCAL_CONFIG_DIR).exists()
        assert (temp_project_dir / ModeSync.LOCAL_CONFIG_DIR).is_dir()
        
    def test_sync_modes_to_local_target(self, sync_manager, temp_modes_dir, temp_project_dir):
        """Test syncing modes to a local project directory."""
        # Setup
        modes = ['code', 'debug', 'custom-mode']
        for mode in modes:
            self.create_mode_file(
                temp_modes_dir,
                mode,
                self.create_valid_mode_config(mode)
            )
        
        sync_manager.set_local_config_path(temp_project_dir)
        
        # Test
        success = sync_manager.sync_modes()
        
        # Verify
        assert success is True
        local_config_file = temp_project_dir / ModeSync.LOCAL_CONFIG_DIR / ModeSync.LOCAL_CONFIG_FILE
        assert local_config_file.exists()
        
        with open(local_config_file, 'r') as f:
            content = f.read()
            for mode in modes:
                assert f'slug: {mode}' in content
                
    def test_backup_local_config(self, sync_manager, temp_project_dir):
        """Test backup of existing local config."""
        # Setup
        sync_manager.set_local_config_path(temp_project_dir)
        local_config_dir = temp_project_dir / ModeSync.LOCAL_CONFIG_DIR
        local_config_dir.mkdir(parents=True, exist_ok=True)
        
        local_config_file = local_config_dir / ModeSync.LOCAL_CONFIG_FILE
        with open(local_config_file, 'w') as f:
            f.write("customModes: []\n")
        
        # Test
        success = sync_manager.backup_existing_config()
        
        # Verify
        assert success is True
        backup_path = local_config_file.with_suffix('.yaml.backup')
        assert backup_path.exists()
        
    def test_validate_target_directory(self, sync_manager, temp_project_dir):
        """Test validation of target directory."""
        # Valid directory
        assert sync_manager.validate_target_directory(temp_project_dir) is True
        
        # Non-existent directory
        non_existent = temp_project_dir / "non_existent"
        with pytest.raises(SyncError):
            sync_manager.validate_target_directory(non_existent)
        
        # File instead of directory
        test_file = temp_project_dir / "test.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        with pytest.raises(SyncError):
            sync_manager.validate_target_directory(test_file)
            
    # MCP Interface Tests
    
    def test_sync_from_dict(self, sync_manager, temp_modes_dir, temp_project_dir):
        """Test syncing modes from a dictionary configuration."""
        # Setup
        modes = ['code', 'debug']
        for mode in modes:
            self.create_mode_file(
                temp_modes_dir,
                mode,
                self.create_valid_mode_config(mode)
            )
            
        # Create MCP request parameters
        params = {
            "target": str(temp_project_dir),
            "strategy": "alphabetical",
            "options": {
                "priority_first": ["debug"],
                "exclude": []
            }
        }
        
        # Test
        result = sync_manager.sync_from_dict(params)
        
        # Verify
        assert result["success"] is True
        assert "message" in result
        
        local_config_file = temp_project_dir / ModeSync.LOCAL_CONFIG_DIR / ModeSync.LOCAL_CONFIG_FILE
        assert local_config_file.exists()
        
        with open(local_config_file, 'r') as f:
            content = f.read()
            for mode in modes:
                assert f'slug: {mode}' in content
                
    def test_sync_from_dict_missing_target(self, sync_manager):
        """Test syncing modes with missing target parameter."""
        # Create MCP request with missing target
        params = {
            "strategy": "alphabetical",
            "options": {}
        }
        
        # Test
        result = sync_manager.sync_from_dict(params)
        
        # Verify
        assert result["success"] is False
        assert "error" in result
        assert "target" in result["error"]
        
    def test_sync_from_dict_invalid_strategy(self, sync_manager, temp_project_dir):
        """Test syncing modes with invalid strategy."""
        # Create MCP request with invalid strategy
        params = {
            "target": str(temp_project_dir),
            "strategy": "invalid_strategy",
            "options": {}
        }
        
        # Test
        result = sync_manager.sync_from_dict(params)
        
        # Verify
        assert result["success"] is False
        assert "error" in result
        assert "strategy" in result["error"]
        
    def test_get_sync_status(self, sync_manager, temp_modes_dir):
        """Test getting sync status."""
        # Setup
        modes = ['code', 'debug', 'custom-mode']
        for mode in modes:
            self.create_mode_file(
                temp_modes_dir,
                mode,
                self.create_valid_mode_config(mode)
            )
            
        # Test
        status = sync_manager.get_sync_status()
        
        # Verify
        assert "mode_count" in status
        assert status["mode_count"] == len(modes)
        assert "categories" in status
        assert len(status["categories"]) > 0
        assert "modes" in status
        assert len(status["modes"]) == len(modes)
    
    def test_sync_modes_with_config_write_error(self, sync_manager, temp_modes_dir, temp_config_dir, monkeypatch):
        """Test sync process with config write error."""
        # Create a valid mode
        self.create_mode_file(
            temp_modes_dir,
            'test-mode',
            self.create_valid_mode_config('test-mode')
        )
        
        # Set global config path
        config_path = temp_config_dir / "custom_modes.yaml"
        sync_manager.set_global_config_path(config_path)
        
        # Mock write_config to fail
        def mock_write_config(*args, **kwargs):
            return False
            
        monkeypatch.setattr(sync_manager, 'write_config', mock_write_config)
        
        success = sync_manager.sync_modes()
        assert success is False