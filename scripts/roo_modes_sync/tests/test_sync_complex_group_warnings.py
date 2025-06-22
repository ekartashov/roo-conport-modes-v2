#!/usr/bin/env python3
"""
Test cases for sync script integration with complex group warning functionality.

Tests that the sync script properly detects complex group notation in existing
global configs and warns about information being stripped during sync.
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Try relative imports first, fall back to absolute imports
try:
    from ..core.sync import ModeSync
    from ..exceptions import SyncError
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from core.sync import ModeSync
    from exceptions import SyncError


class TestSyncComplexGroupWarnings:
    """Test class for sync script complex group warning functionality."""
    
    @pytest.fixture
    def temp_modes_dir(self):
        """Create a temporary directory with test mode files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            modes_dir = Path(temp_dir) / "modes"
            modes_dir.mkdir()
            
            # Create a simple test mode
            test_mode = {
                'slug': 'test-mode',
                'name': 'Test Mode',
                'roleDefinition': 'A test mode',
                'groups': ['read', 'edit']
            }
            
            with open(modes_dir / "test-mode.yaml", 'w') as f:
                yaml.dump(test_mode, f)
            
            yield modes_dir
    
    @pytest.fixture
    def temp_global_config_with_complex_groups(self):
        """Create a temporary global config file with complex groups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "custom_modes.yaml"
            
            # Create config with complex groups that would be stripped
            complex_config = {
                'customModes': [
                    {
                        'slug': 'architect',
                        'name': 'Architect Mode',
                        'roleDefinition': 'Architecture planning',
                        'groups': [
                            'read',
                            {
                                'edit': {
                                    'fileRegex': '\\.md$',
                                    'description': 'Only markdown files'
                                }
                            },
                            'browser'
                        ]
                    },
                    {
                        'slug': 'code',
                        'name': 'Code Mode', 
                        'roleDefinition': 'Code implementation',
                        'groups': [
                            'read',
                            {
                                'edit': {
                                    'fileRegex': '\\.(js|ts|py)$',
                                    'description': 'Code files only'
                                }
                            },
                            'command'
                        ]
                    }
                ]
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(complex_config, f)
            
            yield config_path
    
    @pytest.fixture
    def temp_empty_global_config(self):
        """Create a temporary empty global config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "custom_modes.yaml"
            config_path.touch()  # Create empty file
            yield config_path
    
    @pytest.fixture
    def sync_instance(self, temp_modes_dir):
        """Create a ModeSync instance for testing."""
        return ModeSync(temp_modes_dir)
    
    def test_check_for_complex_groups_and_warn_with_complex_groups(self, sync_instance, temp_global_config_with_complex_groups):
        """Test that complex groups are detected and warnings are generated."""
        # Set the global config path
        sync_instance.set_global_config_path(temp_global_config_with_complex_groups)
        
        # Check for complex groups
        result = sync_instance.check_for_complex_groups_and_warn()
        
        # Assertions
        assert result['has_complex_groups'] is True
        assert 'architect' in result['stripped_information']
        assert 'code' in result['stripped_information']
        
        # Check architect mode stripped info
        architect_stripped = result['stripped_information']['architect']
        assert len(architect_stripped) == 1
        assert architect_stripped[0]['fileRegex'] == '\\.md$'
        assert architect_stripped[0]['description'] == 'Only markdown files'
        
        # Check code mode stripped info
        code_stripped = result['stripped_information']['code']
        assert len(code_stripped) == 1
        assert code_stripped[0]['fileRegex'] == '\\.(js|ts|py)$'
        assert code_stripped[0]['description'] == 'Code files only'
        
        # Check warning messages
        assert len(result['warning_messages']) > 0
        warning_text = '\n'.join(result['warning_messages'])
        assert 'architect' in warning_text.lower()
        assert 'code' in warning_text.lower()
        assert 'fileRegex' in warning_text
        assert 'description' in warning_text
    
    def test_check_for_complex_groups_and_warn_with_no_complex_groups(self, sync_instance, temp_empty_global_config):
        """Test that no warnings are generated when no complex groups exist."""
        # Set the global config path
        sync_instance.set_global_config_path(temp_empty_global_config)
        
        # Check for complex groups
        result = sync_instance.check_for_complex_groups_and_warn()
        
        # Assertions
        assert result['has_complex_groups'] is False
        assert result['stripped_information'] == {}
        assert result['warning_messages'] == []
    
    def test_check_for_complex_groups_and_warn_with_nonexistent_config(self, sync_instance):
        """Test that no warnings are generated when config file doesn't exist."""
        # Set a non-existent config path
        nonexistent_path = Path("/tmp/nonexistent/custom_modes.yaml")
        sync_instance.set_global_config_path(nonexistent_path)
        
        # Check for complex groups
        result = sync_instance.check_for_complex_groups_and_warn()
        
        # Assertions
        assert result['has_complex_groups'] is False
        assert result['stripped_information'] == {}
        assert result['warning_messages'] == []
    
    def test_sync_modes_generates_warnings_for_complex_groups(self, sync_instance, temp_global_config_with_complex_groups):
        """Test that sync_modes method generates warnings when complex groups will be stripped."""
        # Set the global config path
        sync_instance.set_global_config_path(temp_global_config_with_complex_groups)
        
        # Mock logger to capture warning messages
        with patch('roo_modes_sync.core.sync.logger') as mock_logger:
            # Perform sync (dry run to avoid actually writing)
            result = sync_instance.sync_modes(dry_run=True)
            
            # Should succeed
            assert result is True
            
            # Check that warnings were logged
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if 'complex group' in str(call).lower() or 'stripped' in str(call).lower()]
            assert len(warning_calls) > 0
    
    def test_sync_modes_with_warnings_option_enabled(self, sync_instance, temp_global_config_with_complex_groups):
        """Test sync_modes with enable_complex_group_warnings option."""
        # Set the global config path
        sync_instance.set_global_config_path(temp_global_config_with_complex_groups)
        
        # Perform sync with warnings enabled
        options = {'enable_complex_group_warnings': True}
        
        with patch('roo_modes_sync.core.sync.logger') as mock_logger:
            result = sync_instance.sync_modes(options=options, dry_run=True)
            
            # Should succeed
            assert result is True
            
            # Check that complex group warnings were logged
            all_calls = mock_logger.warning.call_args_list + mock_logger.info.call_args_list
            warning_found = any('complex group' in str(call).lower() or 'stripped' in str(call).lower() 
                              for call in all_calls)
            assert warning_found
    
    def test_sync_modes_with_warnings_option_disabled(self, sync_instance, temp_global_config_with_complex_groups):
        """Test sync_modes with enable_complex_group_warnings option disabled."""
        # Set the global config path
        sync_instance.set_global_config_path(temp_global_config_with_complex_groups)
        
        # Perform sync with warnings disabled
        options = {'enable_complex_group_warnings': False}
        
        with patch('roo_modes_sync.core.sync.logger') as mock_logger:
            result = sync_instance.sync_modes(options=options, dry_run=True)
            
            # Should succeed
            assert result is True
            
            # Check that complex group warnings were NOT logged
            all_calls = mock_logger.warning.call_args_list + mock_logger.info.call_args_list
            warning_found = any('complex group' in str(call).lower() or 'stripped' in str(call).lower() 
                              for call in all_calls)
            assert not warning_found
    
    def test_sync_modes_default_behavior_shows_warnings(self, sync_instance, temp_global_config_with_complex_groups):
        """Test that sync_modes shows complex group warnings by default."""
        # Set the global config path
        sync_instance.set_global_config_path(temp_global_config_with_complex_groups)
        
        with patch('roo_modes_sync.core.sync.logger') as mock_logger:
            result = sync_instance.sync_modes(dry_run=True)
            
            # Should succeed
            assert result is True
            
            # Check that warnings were logged by default
            all_calls = mock_logger.warning.call_args_list + mock_logger.info.call_args_list
            warning_found = any('complex group' in str(call).lower() or 'stripped' in str(call).lower() 
                              for call in all_calls)
            assert warning_found
    
    def test_write_config_preserves_warning_functionality(self, sync_instance, temp_global_config_with_complex_groups):
        """Test that write_config method calls the complex group warning check."""
        # Set the global config path
        sync_instance.set_global_config_path(temp_global_config_with_complex_groups)
        
        # Create a simple config to write
        simple_config = {
            'customModes': [
                {
                    'slug': 'test',
                    'name': 'Test Mode',
                    'roleDefinition': 'Test role',
                    'groups': ['read', 'edit']
                }
            ]
        }
        
        # Mock the warning check method to verify it's called
        with patch.object(sync_instance, 'check_for_complex_groups_and_warn') as mock_check:
            mock_check.return_value = {
                'has_complex_groups': True,
                'stripped_information': {'test': []},
                'warning_messages': ['Test warning']
            }
            
            # Call write_config in dry run mode (we'll test actual writing separately)
            with patch('builtins.open', MagicMock()):
                with patch('roo_modes_sync.core.sync.yaml.dump', MagicMock()):
                    with patch('roo_modes_sync.core.sync.logger') as mock_logger:
                        sync_instance.write_config(simple_config)
                        
                        # Verify the warning check was called
                        mock_check.assert_called_once()
                        
                        # Verify warnings were logged
                        warning_calls = mock_logger.warning.call_args_list
                        assert len(warning_calls) > 0

    def test_write_config_applies_global_config_fixer_transformation(self, sync_instance):
        """Test that write_config method applies GlobalConfigFixer transformation to complex groups."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            sync_instance.set_global_config_path(config_path)
            
            # Create config with complex groups that need fixing
            complex_config = {
                'customModes': [
                    {
                        'slug': 'architect',
                        'name': 'Architect Mode',
                        'roleDefinition': 'Architecture planning',
                        'groups': [
                            'read',
                            {
                                'edit': {
                                    'fileRegex': '\\.md$',
                                    'description': 'Only markdown files'
                                }
                            },
                            'browser'
                        ]
                    },
                    {
                        'slug': 'simple-mode',
                        'name': 'Simple Mode',
                        'roleDefinition': 'Simple mode with no complex groups',
                        'groups': ['read', 'edit']
                    }
                ]
            }
            
            # Write the config using write_config method (this should apply the fix)
            with patch('roo_modes_sync.core.sync.logger'):  # Suppress warnings for test
                result = sync_instance.write_config(complex_config)
                
            # Should succeed
            assert result is True
            assert config_path.exists()
            
            # Read back the written config and verify transformation was applied
            with open(config_path, 'r') as f:
                written_content = f.read()
                written_config = yaml.safe_load(written_content)
            
            # Verify the complex groups were transformed to simple groups
            architect_mode = None
            simple_mode = None
            
            for mode in written_config['customModes']:
                if mode['slug'] == 'architect':
                    architect_mode = mode
                elif mode['slug'] == 'simple-mode':
                    simple_mode = mode
            
            assert architect_mode is not None
            assert simple_mode is not None
            
            # Architect mode should have complex groups converted to simple groups
            architect_groups = architect_mode['groups']
            assert isinstance(architect_groups, list)
            assert all(isinstance(group, str) for group in architect_groups)
            assert 'read' in architect_groups
            assert 'edit' in architect_groups  # Complex edit group should be simplified to 'edit'
            assert 'browser' in architect_groups
            
            # Simple mode should remain unchanged
            simple_groups = simple_mode['groups']
            assert simple_groups == ['read', 'edit']
            
            # Verify no complex group objects remain in the written config
            for mode in written_config['customModes']:
                for group in mode['groups']:
                    assert isinstance(group, str), f"Found non-string group in {mode['slug']}: {group}"

    def test_write_config_transformation_preserves_non_group_fields(self, sync_instance):
        """Test that GlobalConfigFixer transformation preserves all non-group fields."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            sync_instance.set_global_config_path(config_path)
            
            # Create config with complex groups and additional fields
            complex_config = {
                'customModes': [
                    {
                        'slug': 'test-mode',
                        'name': 'Test Mode',
                        'roleDefinition': 'Test mode with complex groups',
                        'groups': [
                            'read',
                            {
                                'edit': {
                                    'fileRegex': '\\.(py|ts)$',
                                    'description': 'Code files'
                                }
                            }
                        ],
                        'source': 'local',
                        'customField': 'custom_value',
                        'metadata': {
                            'author': 'test',
                            'version': '1.0'
                        }
                    }
                ]
            }
            
            # Write the config using write_config method
            with patch('roo_modes_sync.core.sync.logger'):  # Suppress warnings for test
                result = sync_instance.write_config(complex_config)
                
            assert result is True
            
            # Read back and verify all fields preserved except groups are simplified
            with open(config_path, 'r') as f:
                written_config = yaml.safe_load(f.read())
            
            mode = written_config['customModes'][0]
            
            # All non-group fields should be preserved exactly
            assert mode['slug'] == 'test-mode'
            assert mode['name'] == 'Test Mode'
            assert mode['roleDefinition'] == 'Test mode with complex groups'
            assert mode['source'] == 'local'
            assert mode['customField'] == 'custom_value'
            assert mode['metadata'] == {'author': 'test', 'version': '1.0'}
            
            # Groups should be simplified
            assert mode['groups'] == ['read', 'edit']  # Complex edit group simplified


if __name__ == '__main__':
    pytest.main([__file__])