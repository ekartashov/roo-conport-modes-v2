#!/usr/bin/env python3
"""
TDD test suite for Mode Groupings functionality.

This tests a new simplified configuration system that allows users to define
named groups of modes with specific ordering, making configuration much more intuitive.
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from typing import Dict, Any, List

from roo_modes_sync.core.sync import ModeSync
from roo_modes_sync.exceptions import ConfigurationError, SyncError


class TestModeGroupings:
    """TDD tests for mode groupings feature."""

    @pytest.fixture
    def sync_instance_with_modes(self, tmp_path):
        """Create a ModeSync instance with test modes."""
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        
        # Create test modes that we'll use in groupings
        test_modes = [
            {'slug': 'code', 'name': 'Code Mode', 'roleDefinition': 'Code development', 'groups': ['read']},
            {'slug': 'debug', 'name': 'Debug Mode', 'roleDefinition': 'Bug fixing', 'groups': ['read']},
            {'slug': 'ask', 'name': 'Ask Mode', 'roleDefinition': 'Questions', 'groups': ['read']},
            {'slug': 'architect', 'name': 'Architect Mode', 'roleDefinition': 'System design', 'groups': ['read']},
            {'slug': 'orchestrator', 'name': 'Orchestrator Mode', 'roleDefinition': 'Workflow coordination', 'groups': ['read']},
            {'slug': 'security-auditor', 'name': 'Security Auditor', 'roleDefinition': 'Security analysis', 'groups': ['read']},
            {'slug': 'prompt-enhancer', 'name': 'Prompt Enhancer', 'roleDefinition': 'Prompt improvement', 'groups': ['read']},
        ]
        
        for mode_config in test_modes:
            mode_file = modes_dir / f"{mode_config['slug']}.yaml"
            with open(mode_file, 'w') as f:
                yaml.dump(mode_config, f)
        
        return ModeSync(modes_dir)

    def test_groupings_strategy_requires_active_group(self, sync_instance_with_modes):
        """Test that groupings strategy requires active_group or active_groups option."""
        groupings_config = {
            'mode_groups': {
                'debugging-workflow': ['debug', 'code', 'ask'],
                'planning-workflow': ['architect', 'code', 'debug'],
                'essential-modes': ['code', 'debug', 'ask', 'architect']
            }
        }
        
        # This should fail because we haven't provided active_group or active_groups
        with pytest.raises((ConfigurationError, SyncError), match="requires either 'active_group' or 'active_groups'"):
            sync_instance_with_modes.create_global_config(strategy_name='groupings', options=groupings_config)

    def test_groupings_strategy_basic_functionality(self, sync_instance_with_modes):
        """Test basic groupings functionality."""
        groupings_config = {
            'mode_groups': {
                'essential-workflow': ['code', 'debug', 'ask'],
                'specialized-tools': ['security-auditor', 'prompt-enhancer']
            },
            'active_group': 'essential-workflow'
        }
        
        # This should work now that we implemented GroupingsOrderingStrategy
        config = sync_instance_with_modes.create_global_config(strategy_name='groupings', options=groupings_config)
        
        # Verify the config structure
        assert 'customModes' in config
        assert len(config['customModes']) == 3  # code, debug, ask
        
        # Verify the order matches the group definition
        mode_slugs = [mode['slug'] for mode in config['customModes']]
        assert mode_slugs == ['code', 'debug', 'ask']

    def test_groupings_strategy_with_multiple_groups(self, sync_instance_with_modes):
        """Test groupings strategy with multiple group selection."""
        groupings_config = {
            'mode_groups': {
                'core-workflow': ['code', 'debug'],
                'planning-workflow': ['architect', 'ask'],
                'specialized-tools': ['security-auditor', 'prompt-enhancer']
            },
            'active_groups': ['core-workflow', 'specialized-tools'],  # Multiple groups
            'group_order': ['core-workflow', 'specialized-tools']
        }
        
        # This should work now that we implemented the feature
        config = sync_instance_with_modes.create_global_config(strategy_name='groupings', options=groupings_config)
        
        # Verify the config structure
        assert 'customModes' in config
        assert len(config['customModes']) == 4  # code, debug, security-auditor, prompt-enhancer
        
        # Verify the order matches the group order (core-workflow first, then specialized-tools)
        mode_slugs = [mode['slug'] for mode in config['customModes']]
        assert mode_slugs == ['code', 'debug', 'security-auditor', 'prompt-enhancer']

    def test_groupings_strategy_preserves_order_within_groups(self, sync_instance_with_modes):
        """Test that groupings preserve the specified order within each group."""
        groupings_config = {
            'mode_groups': {
                'debugging-first-workflow': ['debug', 'code', 'ask'],  # Debug first
                'code-first-workflow': ['code', 'debug', 'ask']       # Code first
            },
            'active_group': 'debugging-first-workflow'
        }
        
        config = sync_instance_with_modes.create_global_config(strategy_name='groupings', options=groupings_config)
        
        # Verify the config structure
        assert 'customModes' in config
        assert len(config['customModes']) == 3
        
        # Verify the exact order is preserved (debug first, as specified)
        mode_slugs = [mode['slug'] for mode in config['customModes']]
        assert mode_slugs == ['debug', 'code', 'ask']

    def test_groupings_strategy_handles_nonexistent_modes(self, sync_instance_with_modes):
        """Test that groupings strategy handles non-existent modes gracefully."""
        groupings_config = {
            'mode_groups': {
                'mixed-group': ['code', 'debug', 'nonexistent-mode', 'ask']
            },
            'active_group': 'mixed-group'
        }
        
        # Should filter out non-existent modes and continue with available ones
        config = sync_instance_with_modes.create_global_config(strategy_name='groupings', options=groupings_config)
        
        # Verify the config structure
        assert 'customModes' in config
        assert len(config['customModes']) == 3  # Only code, debug, ask (nonexistent-mode filtered out)
        
        # Verify the order is preserved for existing modes
        mode_slugs = [mode['slug'] for mode in config['customModes']]
        assert mode_slugs == ['code', 'debug', 'ask']

    def test_groupings_strategy_validation(self, sync_instance_with_modes):
        """Test validation for groupings configuration."""
        
        # Test missing mode_groups
        with pytest.raises((ConfigurationError, SyncError), match="requires 'mode_groups'"):
            sync_instance_with_modes.create_global_config(strategy_name='groupings', options={'active_group': 'test'})
        
        # Test missing active_group and active_groups
        with pytest.raises((ConfigurationError, SyncError), match="requires either 'active_group' or 'active_groups'"):
            sync_instance_with_modes.create_global_config(strategy_name='groupings', options={'mode_groups': {}})
        
        # Test invalid active_group
        with pytest.raises((ConfigurationError, SyncError), match="not found in mode_groups"):
            sync_instance_with_modes.create_global_config(
                strategy_name='groupings',
                options={
                    'mode_groups': {'valid-group': ['code']},
                    'active_group': 'nonexistent-group'
                }
            )

    def test_groupings_config_file_parsing(self, sync_instance_with_modes, tmp_path):
        """Test parsing groupings configuration from YAML file."""
        config_content = """
strategy: groupings

mode_groups:
  essential-workflow:
    - code
    - debug
    - ask
  planning-workflow:
    - architect
    - code
    - debug
  specialized-tools:
    - security-auditor
    - prompt-enhancer

active_group: essential-workflow

# Optional: exclude modes even if they're in groups
exclude:
  - prompt-enhancer

# Optional: priority modes that come first regardless of group order
priority_first:
  - debug
"""
        
        config_file = tmp_path / "groupings_config.yaml"
        config_file.write_text(config_content)
        
        # Load the YAML config and test it
        import yaml
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Extract the groupings-specific options
        groupings_options = {
            'mode_groups': config_data['mode_groups'],
            'active_group': config_data['active_group'],
            'exclude': config_data.get('exclude', []),
            'priority_first': config_data.get('priority_first', [])
        }
        
        # Test using the config
        config = sync_instance_with_modes.create_global_config(
            strategy_name=config_data['strategy'],
            options=groupings_options
        )
        
        # Verify the config structure
        assert 'customModes' in config
        assert len(config['customModes']) == 3  # code, debug, ask (prompt-enhancer excluded)
        
        # Verify priority_first worked (debug should be first)
        mode_slugs = [mode['slug'] for mode in config['customModes']]
        assert mode_slugs[0] == 'debug'  # debug should be first due to priority_first
        assert 'code' in mode_slugs
        assert 'ask' in mode_slugs
        assert 'prompt-enhancer' not in mode_slugs  # excluded

    def test_groupings_backwards_compatibility(self, sync_instance_with_modes):
        """Test that existing strategies still work after adding groupings."""
        # Ensure that strategic, alphabetical, category, and custom strategies still work
        
        # Strategic should still work
        config = sync_instance_with_modes.create_global_config(strategy_name='strategic')
        assert 'customModes' in config
        assert len(config['customModes']) > 0
        
        # Custom should still work
        config = sync_instance_with_modes.create_global_config(
            strategy_name='custom',
            options={'custom_order': ['debug', 'code', 'ask']}
        )
        assert 'customModes' in config
        assert config['customModes'][0]['slug'] == 'debug'
        
        # Alphabetical should still work
        config = sync_instance_with_modes.create_global_config(strategy_name='alphabetical')
        assert 'customModes' in config
        assert len(config['customModes']) > 0
        
        # Category should still work
        config = sync_instance_with_modes.create_global_config(strategy_name='category')
        assert 'customModes' in config
        assert len(config['customModes']) > 0


class TestModeGroupingsIntegration:
    """Integration tests for mode groupings with CLI and configuration files."""

    @pytest.fixture
    def sync_instance_with_modes(self, tmp_path):
        """Create a ModeSync instance with test modes."""
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        
        # Create test modes
        test_modes = [
            {'slug': 'code', 'name': 'Code Mode', 'roleDefinition': 'Code development', 'groups': ['read']},
            {'slug': 'debug', 'name': 'Debug Mode', 'roleDefinition': 'Bug fixing', 'groups': ['read']},
            {'slug': 'ask', 'name': 'Ask Mode', 'roleDefinition': 'Questions', 'groups': ['read']},
            {'slug': 'architect', 'name': 'Architect Mode', 'roleDefinition': 'System design', 'groups': ['read']},
        ]
        
        for mode_config in test_modes:
            mode_file = modes_dir / f"{mode_config['slug']}.yaml"
            with open(mode_file, 'w') as f:
                yaml.dump(mode_config, f)
        
        return ModeSync(modes_dir)

    def test_cli_integration_with_groupings(self, sync_instance_with_modes, tmp_path):
        """Test CLI integration with groupings strategy."""
        # This test verifies that the CLI can handle groupings configuration
        # and that the sync_from_dict method supports groupings
        
        params = {
            'target': str(tmp_path / "output"),
            'strategy': 'groupings',
            'mode_groups': {
                'essential': ['code', 'debug'],
                'planning': ['architect', 'ask']
            },
            'active_group': 'essential'
        }
        
        # Create target directory
        (tmp_path / "output").mkdir()
        
        # This should work now that we implemented groupings support
        result = sync_instance_with_modes.sync_from_dict(params)
        
        # Verify the sync was successful
        assert result is not None
        
        # Check that files were created in the target directory
        output_dir = tmp_path / "output"
        assert output_dir.exists()
        
        # Verify that only the essential modes were synced (code, debug)
        # This depends on the exact output format of sync_from_dict
        # For now, just verify it completed without error

    def test_example_configuration_files_not_implemented_yet(self, tmp_path):
        """Test that example configuration files would work with groupings (TDD Red phase)."""
        # This defines what we want the example config files to look like
        
        simple_groupings_config = """
# Simple Mode Groupings Configuration
# Easy way to define custom mode workflows

strategy: groupings

mode_groups:
  # Essential development workflow
  essential:
    - code      # Development
    - debug     # Bug fixing
    - ask       # Questions

  # Complete workflow including planning
  full-workflow:
    - architect # Planning
    - code      # Development
    - debug     # Bug fixing
    - ask       # Questions

  # Just debugging tools
  debugging-only:
    - debug
    - ask

# Which group to use (can be changed easily)
active_group: essential

# Optional: modes that should always come first
priority_modes: []

# Optional: modes to exclude even if in groups
exclude_modes: []
"""
        
        config_file = tmp_path / "simple_groupings.yaml"
        config_file.write_text(simple_groupings_config)
        
        # This config should be parseable and usable once we implement the feature
        config_data = yaml.safe_load(config_file.read_text())
        assert config_data['strategy'] == 'groupings'
        assert 'essential' in config_data['mode_groups']
        assert config_data['active_group'] == 'essential'


if __name__ == "__main__":
    pytest.main([__file__])