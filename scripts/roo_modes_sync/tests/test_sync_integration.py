#!/usr/bin/env python3
"""
Integration tests for the sync system with development metadata handling.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

from roo_modes_sync.core.sync import ModeSync
from roo_modes_sync.core.validation import ModeValidator


class TestSyncIntegration:
    """Test sync system integration with development metadata functionality."""
    
    def test_sync_strips_development_metadata_from_real_modes(self, tmp_path):
        """Test that sync system properly strips development metadata from real mode files."""
        # Create a temporary modes directory with a test mode file
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        
        # Create a mode file with development metadata (like real mode files)
        mode_config = {
            'slug': 'test-mode',
            'name': 'Test Mode',
            'roleDefinition': 'A test mode for validation',
            'groups': ['read', 'edit'],
            'source': 'local',  # Development metadata
            'model': 'claude-sonnet-4'  # Development metadata
        }
        
        mode_file = modes_dir / "test-mode.yaml"
        with open(mode_file, 'w') as f:
            yaml.dump(mode_config, f)
        
        # Initialize sync system
        sync = ModeSync(modes_dir)
        sync.set_options({'collect_warnings': True, 'continue_on_validation_error': False})
        
        # Load the mode config - should strip development metadata
        loaded_config = sync.load_mode_config('test-mode')
        
        # Verify development metadata was stripped except for source='global'
        assert loaded_config['slug'] == 'test-mode'
        assert loaded_config['name'] == 'Test Mode'
        assert loaded_config['roleDefinition'] == 'A test mode for validation'
        assert loaded_config['groups'] == ['read', 'edit']
        assert loaded_config['source'] == 'global'  # Should be overwritten
        assert 'model' not in loaded_config  # Should be stripped
    
    def test_validation_accepts_development_metadata_but_strips_for_output(self, tmp_path):
        """Test that validation accepts development metadata but sync output is clean."""
        # Create a temporary modes directory
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        
        # Create a mode file with development metadata
        mode_config = {
            'slug': 'dev-test',
            'name': 'Development Test Mode',
            'roleDefinition': 'A mode with development metadata',
            'whenToUse': 'For testing development metadata handling',
            'groups': ['read'],
            'source': 'local',
            'model': 'claude-sonnet-4'
        }
        
        mode_file = modes_dir / "dev-test.yaml"
        with open(mode_file, 'w') as f:
            yaml.dump(mode_config, f)
        
        # Initialize validator
        validator = ModeValidator()
        
        # Validation should pass (no exceptions raised)
        result = validator.validate_mode_config(mode_config, str(mode_file), collect_warnings=True)
        assert result.valid
        
        # Check that no warnings about development metadata fields
        dev_field_warnings = [w for w in result.warnings 
                            if any(field in w['message'] for field in ['source', 'model'])]
        assert len(dev_field_warnings) == 0, f"Unexpected warnings about dev fields: {dev_field_warnings}"
        
        # Strip development metadata
        stripped_config = validator.strip_development_metadata(mode_config)
        
        # Verify only development metadata was removed
        expected_keys = {'slug', 'name', 'roleDefinition', 'whenToUse', 'groups'}
        assert set(stripped_config.keys()) == expected_keys
        assert 'source' not in stripped_config
        assert 'model' not in stripped_config
    
    def test_create_global_config_with_development_metadata_stripping(self, tmp_path):
        """Test that create_global_config properly handles development metadata."""
        # Create modes directory with test modes
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        
        # Create multiple mode files with development metadata
        for i, (slug, model) in enumerate([('mode1', 'claude-sonnet-4'), ('mode2', 'gpt-4')]):
            mode_config = {
                'slug': slug,
                'name': f'Test Mode {i+1}',
                'roleDefinition': f'Test mode {i+1} description',
                'groups': ['read', 'edit'],
                'source': 'local',
                'model': model
            }
            
            mode_file = modes_dir / f"{slug}.yaml"
            with open(mode_file, 'w') as f:
                yaml.dump(mode_config, f)
        
        # Initialize sync system
        sync = ModeSync(modes_dir)
        sync.set_options({'collect_warnings': True, 'continue_on_validation_error': False})
        
        # Create global config
        config = sync.create_global_config('strategic')
        
        # Verify the config was created successfully
        assert 'customModes' in config
        assert len(config['customModes']) == 2
        
        # Verify each mode has development metadata stripped and source set correctly
        for mode in config['customModes']:
            assert mode['source'] == 'global'
            assert 'model' not in mode
            assert all(field in mode for field in ['slug', 'name', 'roleDefinition', 'groups'])
    
    def test_backward_compatibility_with_existing_modes(self, tmp_path):
        """Test that existing modes without development metadata still work."""
        # Create modes directory
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        
        # Create a clean mode file (like template modes)
        clean_mode_config = {
            'slug': 'clean-mode',
            'name': 'Clean Mode',
            'roleDefinition': 'A mode without development metadata',
            'groups': ['read']
        }
        
        mode_file = modes_dir / "clean-mode.yaml"
        with open(mode_file, 'w') as f:
            yaml.dump(clean_mode_config, f)
        
        # Initialize sync system
        sync = ModeSync(modes_dir)
        sync.set_options({'collect_warnings': True, 'continue_on_validation_error': False})
        
        # Load the mode config
        loaded_config = sync.load_mode_config('clean-mode')
        
        # Verify the mode loads correctly and gets source='global' added
        assert loaded_config['slug'] == 'clean-mode'
        assert loaded_config['name'] == 'Clean Mode'
        assert loaded_config['roleDefinition'] == 'A mode without development metadata'
        assert loaded_config['groups'] == ['read']
        assert loaded_config['source'] == 'global'  # Should be added
        assert 'model' not in loaded_config  # Should not exist
    
    def test_unknown_metadata_still_generates_warnings(self, tmp_path):
        """Test that unknown metadata fields (not in development list) still generate warnings."""
        # Create modes directory
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        
        # Create a mode file with unknown metadata
        mode_config = {
            'slug': 'unknown-meta',
            'name': 'Unknown Metadata Mode',
            'roleDefinition': 'A mode with unknown metadata',
            'groups': ['read'],
            'source': 'local',  # Known development metadata
            'unknown_field': 'should cause warning'  # Unknown field
        }
        
        mode_file = modes_dir / "unknown-meta.yaml"
        with open(mode_file, 'w') as f:
            yaml.dump(mode_config, f)
        
        # Initialize sync system
        sync = ModeSync(modes_dir)
        sync.set_options({'collect_warnings': True, 'continue_on_validation_error': False})
        
        # Load the mode config - should generate warning about unknown_field
        with patch('roo_modes_sync.core.sync.logger') as mock_logger:
            loaded_config = sync.load_mode_config('unknown-meta')
            
            # Check that a warning was logged about the unknown field
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if 'unknown_field' in str(call)]
            assert len(warning_calls) > 0, "Expected warning about unknown_field"
        
        # Verify the loaded config
        assert loaded_config['source'] == 'global'
        # Note: unknown_field should still be present since strip_development_metadata
        # only strips known development metadata fields, not all unknown fields
        assert 'unknown_field' in loaded_config  # Unknown fields are preserved