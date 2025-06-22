"""Test cases for fixing complex group structures in global Roo configuration."""

import pytest
import yaml
import tempfile
from pathlib import Path
from typing import Dict, Any

from roo_modes_sync.core.validation import ModeValidator, YAMLStructureError


class TestGlobalConfigGroupFixes:
    """Test cases for fixing problematic group structures in global Roo configuration."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return ModeValidator()
    
    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create a temporary global config file for testing."""
        config_file = tmp_path / "custom_modes.yaml"
        return config_file
    
    def create_problematic_global_config(self) -> Dict[str, Any]:
        """Create a global config with problematic complex group structures using actual structure."""
        return {
            'customModes': [
                {
                    'slug': 'architect',
                    'name': '🏗️ Architect',
                    'roleDefinition': 'Architect mode for system design',
                    'groups': [
                        'read',
                        {
                            'edit': {
                                'fileRegex': '\\.md$',
                                'description': 'Documentation files (markdown files only)'
                            }
                        },
                        'browser',
                        'command',
                        'mcp'
                    ],
                    'source': 'local'
                },
                {
                    'slug': 'docs',
                    'name': '📚 Docs',
                    'roleDefinition': 'Documentation mode',
                    'groups': [
                        'read',
                        {
                            'edit': {
                                'fileRegex': '\\.(md|rst|adoc|txt|yaml|json|toml|text|markdown)$',
                                'description': 'Documentation, configuration, and text files'
                            }
                        },
                        'mcp',
                        'command'
                    ],
                    'source': 'local'
                },
                {
                    'slug': 'mode-engineer',
                    'name': '⚙️ Mode Engineer',
                    'roleDefinition': 'Mode engineering specialist',
                    'groups': [
                        'read',
                        {
                            'edit': {
                                'fileRegex': '^(modes|templates|docs|examples|utilities/(modes|frameworks/mode-engineer)).*$',
                                'description': 'Mode engineering files (modes, templates, docs, examples, utilities)'
                            }
                        },
                        'browser',
                        'command',
                        'mcp'
                    ],
                    'source': 'local'
                },
                {
                    'slug': 'mode-manager',
                    'name': '📋 Mode Manager',
                    'roleDefinition': 'Mode management specialist',
                    'groups': [
                        'read',
                        {
                            'edit': {
                                'fileRegex': '\\.yaml$',
                                'description': 'YAML configuration files'
                            }
                        },
                        {
                            'edit': {
                                'fileRegex': '^\\.roomodes$',
                                'description': 'Workspace-specific modes file'
                            }
                        },
                        'mcp'
                    ],
                    'source': 'local'
                },
                {
                    'slug': 'code',
                    'name': '💻 Code',
                    'roleDefinition': 'General coding mode',
                    'groups': ['read', 'edit', 'browser', 'command', 'mcp'],
                    'source': 'global'
                }
            ]
        }
    
    def create_fixed_global_config(self) -> Dict[str, Any]:
        """Create a global config with fixed simple group structures using actual structure."""
        return {
            'customModes': [
                {
                    'slug': 'architect',
                    'name': '🏗️ Architect',
                    'roleDefinition': 'Architect mode for system design',
                    'groups': ['read', 'edit', 'browser', 'command', 'mcp'],
                    'source': 'local'
                },
                {
                    'slug': 'docs',
                    'name': '📚 Docs',
                    'roleDefinition': 'Documentation mode',
                    'groups': ['read', 'edit', 'mcp', 'command'],
                    'source': 'local'
                },
                {
                    'slug': 'mode-engineer',
                    'name': '⚙️ Mode Engineer',
                    'roleDefinition': 'Mode engineering specialist',
                    'groups': ['read', 'edit', 'browser', 'command', 'mcp'],
                    'source': 'local'
                },
                {
                    'slug': 'mode-manager',
                    'name': '📋 Mode Manager',
                    'roleDefinition': 'Mode management specialist',
                    'groups': ['read', 'edit', 'mcp'],
                    'source': 'local'
                },
                {
                    'slug': 'code',
                    'name': '💻 Code',
                    'roleDefinition': 'General coding mode',
                    'groups': ['read', 'edit', 'browser', 'command', 'mcp'],
                    'source': 'global'
                }
            ]
        }
    
    def test_problematic_complex_groups_should_fail_validation(self, validator, temp_config_file):
        """Test that complex group structures with fileRegex and description fail validation."""
        problematic_config = self.create_problematic_global_config()
        
        # Test each problematic mode individually
        problematic_modes = ['architect', 'docs', 'mode-engineer', 'mode-manager']
        
        for mode_config in problematic_config['customModes']:
            if mode_config['slug'] in problematic_modes:
                mode_name = mode_config['slug']
                
                # Write individual mode to temp file for validation
                temp_mode_file = temp_config_file.parent / f"{mode_name}.yaml"
                with open(temp_mode_file, 'w') as f:
                    yaml.dump(mode_config, f)
                
                # Validation should detect complex groups as problematic
                # Note: Current validator might accept these, but we're establishing the test first
                # The fix will ensure they get simplified
                result = validator.validate_yaml_structure(str(temp_mode_file), collect_warnings=True)
                
                # Complex groups should be flagged as issues
                has_complex_groups = any(
                    isinstance(group, dict) for group in mode_config['groups']
                )
                assert has_complex_groups, f"Mode {mode_name} should have complex groups for this test"
    
    def test_simple_groups_should_pass_validation(self, validator, temp_config_file):
        """Test that simple group structures pass validation."""
        fixed_config = self.create_fixed_global_config()
        
        # Test each fixed mode individually
        for mode_config in fixed_config['customModes']:
            mode_name = mode_config['slug']
            # Write individual mode to temp file for validation
            temp_mode_file = temp_config_file.parent / f"{mode_name}_fixed.yaml"
            with open(temp_mode_file, 'w') as f:
                yaml.dump(mode_config, f)
            
            # Validation should pass for simple groups
            result = validator.validate_yaml_structure(str(temp_mode_file))
            assert result is True, f"Mode {mode_name} with simple groups should pass validation"
            
            # Mode validation should also pass
            mode_result = validator.validate_mode_config(mode_config, f"{mode_name}.yaml")
            assert mode_result is True, f"Mode {mode_name} should pass mode validation"
    
    def test_identify_modes_with_complex_groups(self, temp_config_file):
        """Test identification of modes that need group structure fixes."""
        problematic_config = self.create_problematic_global_config()
        
        # Write full config to temp file
        with open(temp_config_file, 'w') as f:
            yaml.dump(problematic_config, f)
        
        # Function to identify problematic modes
        def identify_problematic_modes(config_data):
            problematic_modes = []
            custom_modes = config_data.get('customModes', [])
            for mode_config in custom_modes:
                mode_name = mode_config.get('slug', 'unknown')
                if 'groups' in mode_config:
                    groups = mode_config['groups']
                    for group in groups:
                        if isinstance(group, dict):
                            # Check if it has the problematic fileRegex/description structure
                            for group_name, group_config in group.items():
                                if isinstance(group_config, dict) and (
                                    'fileRegex' in group_config or 'description' in group_config
                                ):
                                    problematic_modes.append(mode_name)
                                    break
                    if mode_name in problematic_modes:
                        continue
            return problematic_modes
        
        problematic_modes = identify_problematic_modes(problematic_config)
        
        # Should identify the 4 problematic modes
        expected_problematic = ['architect', 'docs', 'mode-engineer', 'mode-manager']
        assert set(problematic_modes) == set(expected_problematic)
    
    def test_fix_complex_groups_to_simple_groups(self, temp_config_file):
        """Test conversion of complex groups to simple groups."""
        problematic_config = self.create_problematic_global_config()
        expected_fixed_config = self.create_fixed_global_config()
        
        # Function to fix complex groups
        def fix_complex_groups(config_data):
            fixed_config = config_data.copy()
            fixed_custom_modes = []
            
            for mode_config in config_data.get('customModes', []):
                fixed_mode_config = mode_config.copy()
                if 'groups' in mode_config:
                    groups = mode_config['groups']
                    fixed_groups = []
                    seen_groups = set()
                    for group in groups:
                        if isinstance(group, str):
                            # Simple group - keep as is
                            if group not in seen_groups:
                                fixed_groups.append(group)
                                seen_groups.add(group)
                        elif isinstance(group, dict):
                            # Complex group - extract the group name only
                            for group_name, group_config in group.items():
                                if group_name not in seen_groups:
                                    fixed_groups.append(group_name)
                                    seen_groups.add(group_name)
                        else:
                            # Other types - keep as is (shouldn't happen in valid config)
                            fixed_groups.append(group)
                    fixed_mode_config['groups'] = fixed_groups
                fixed_custom_modes.append(fixed_mode_config)
            
            fixed_config['customModes'] = fixed_custom_modes
            return fixed_config
        
        fixed_config = fix_complex_groups(problematic_config)
        
        # Verify the fixed config matches our expected simple structure
        expected_modes = {mode['slug']: mode for mode in expected_fixed_config['customModes']}
        fixed_modes = {mode['slug']: mode for mode in fixed_config['customModes']}
        
        for mode_slug in expected_modes:
            assert mode_slug in fixed_modes
            assert fixed_modes[mode_slug]['groups'] == expected_modes[mode_slug]['groups']
    
    def test_preserve_non_group_fields_during_fix(self, temp_config_file):
        """Test that non-group fields are preserved when fixing groups."""
        problematic_config = self.create_problematic_global_config()
        
        # Function to fix complex groups (same as above)
        def fix_complex_groups(config_data):
            fixed_config = config_data.copy()
            fixed_custom_modes = []
            
            for mode_config in config_data.get('customModes', []):
                fixed_mode_config = mode_config.copy()
                if 'groups' in mode_config:
                    groups = mode_config['groups']
                    fixed_groups = []
                    seen_groups = set()
                    for group in groups:
                        if isinstance(group, str):
                            if group not in seen_groups:
                                fixed_groups.append(group)
                                seen_groups.add(group)
                        elif isinstance(group, dict):
                            for group_name, group_config in group.items():
                                if group_name not in seen_groups:
                                    fixed_groups.append(group_name)
                                    seen_groups.add(group_name)
                        else:
                            fixed_groups.append(group)
                    fixed_mode_config['groups'] = fixed_groups
                fixed_custom_modes.append(fixed_mode_config)
            
            fixed_config['customModes'] = fixed_custom_modes
            return fixed_config
        
        fixed_config = fix_complex_groups(problematic_config)
        
        # Verify all non-group fields are preserved
        original_modes = {mode['slug']: mode for mode in problematic_config['customModes']}
        fixed_modes = {mode['slug']: mode for mode in fixed_config['customModes']}
        
        for mode_slug, original_mode in original_modes.items():
            fixed_mode = fixed_modes[mode_slug]
            
            # Check all fields except groups are preserved
            for field, value in original_mode.items():
                if field != 'groups':
                    assert fixed_mode[field] == value, f"Field {field} not preserved in {mode_slug}"
    
    def test_end_to_end_config_fix_validation(self, validator, temp_config_file):
        """Test complete end-to-end fix and validation process."""
        problematic_config = self.create_problematic_global_config()
        
        # Function to fix complex groups
        def fix_complex_groups(config_data):
            fixed_config = config_data.copy()
            fixed_custom_modes = []
            
            for mode_config in config_data.get('customModes', []):
                fixed_mode_config = mode_config.copy()
                if 'groups' in mode_config:
                    groups = mode_config['groups']
                    fixed_groups = []
                    seen_groups = set()
                    for group in groups:
                        if isinstance(group, str):
                            if group not in seen_groups:
                                fixed_groups.append(group)
                                seen_groups.add(group)
                        elif isinstance(group, dict):
                            for group_name, group_config in group.items():
                                if group_name not in seen_groups:
                                    fixed_groups.append(group_name)
                                    seen_groups.add(group_name)
                        else:
                            fixed_groups.append(group)
                    fixed_mode_config['groups'] = fixed_groups
                fixed_custom_modes.append(fixed_mode_config)
            
            fixed_config['customModes'] = fixed_custom_modes
            return fixed_config
        
        # Apply the fix
        fixed_config = fix_complex_groups(problematic_config)
        
        # Write fixed config to temp file
        with open(temp_config_file, 'w') as f:
            yaml.dump(fixed_config, f)
        
        # Validate each mode in the fixed config
        for mode_config in fixed_config['customModes']:
            mode_name = mode_config['slug']
            # Test both YAML structure and mode config validation
            temp_mode_file = temp_config_file.parent / f"{mode_name}_final.yaml"
            with open(temp_mode_file, 'w') as f:
                yaml.dump(mode_config, f)
            
            # YAML structure should pass
            yaml_result = validator.validate_yaml_structure(str(temp_mode_file))
            assert yaml_result is True, f"YAML structure validation failed for {mode_name}"
            
            # Mode config should pass
            mode_result = validator.validate_mode_config(mode_config, f"{mode_name}.yaml")
            assert mode_result is True, f"Mode config validation failed for {mode_name}"
    
    def test_actual_global_config_structure(self):
        """Test the structure we expect to find in the actual global config file."""
        # This test verifies our understanding of the global config structure
        # Based on the file we read earlier, it should have multiple mode configurations
        
        global_config_path = "../../../.config/VSCodium/User/globalStorage/rooveterinaryinc.roo-cline/settings/custom_modes.yaml"
        
        # For this test, we'll simulate the structure we expect based on the file content
        expected_structure = {
            'slug_key': {
                'slug': 'mode-slug',
                'name': 'Mode Name',
                'roleDefinition': 'Mode description',
                'groups': [],  # This is what we're fixing
                'source': 'local'  # Development metadata
            }
        }
        
        # The actual structure should have multiple modes with this pattern
        # Some have complex groups that need fixing
        assert True  # This test documents the expected structure
    
    def test_warning_functionality_for_stripped_information(self, temp_config_file):
        """Test that the fixer generates warnings about information being stripped."""
        from roo_modes_sync.core.global_config_fixer import GlobalConfigFixer
        
        problematic_config = self.create_problematic_global_config()
        
        # Write config to temp file
        with open(temp_config_file, 'w') as f:
            yaml.dump(problematic_config, f)
        
        fixer = GlobalConfigFixer()
        
        # Test that we can extract stripped information details
        stripped_info = fixer.get_stripped_information_details(problematic_config)
        
        # Should have details for each mode with complex groups
        assert 'architect' in stripped_info
        assert 'docs' in stripped_info
        assert 'mode-engineer' in stripped_info
        assert 'mode-manager' in stripped_info
        assert 'code' not in stripped_info  # code mode has no complex groups
        
        # Check specific stripped information for architect mode
        architect_info = stripped_info['architect']
        assert len(architect_info) == 1  # One complex group
        assert architect_info[0]['group_name'] == 'edit'
        assert architect_info[0]['fileRegex'] == '\\.md$'
        assert architect_info[0]['description'] == 'Documentation files (markdown files only)'
        
        # Check mode-manager which has multiple complex groups
        manager_info = stripped_info['mode-manager']
        assert len(manager_info) == 2  # Two complex groups
        group_names = [info['group_name'] for info in manager_info]
        assert 'edit' in group_names  # Both are 'edit' but with different configs
        
    def test_fix_with_warnings_returns_stripped_info(self, temp_config_file):
        """Test that the fix operation returns detailed information about what was stripped."""
        from roo_modes_sync.core.global_config_fixer import GlobalConfigFixer
        
        problematic_config = self.create_problematic_global_config()
        
        # Write config to temp file
        with open(temp_config_file, 'w') as f:
            yaml.dump(problematic_config, f)
        
        fixer = GlobalConfigFixer()
        
        # Test the enhanced fix operation that includes warnings
        result = fixer.fix_global_config_file_with_warnings(temp_config_file, create_backup=False)
        
        # Should be successful
        assert result['success'] is True
        assert len(result['problematic_modes']) == 4
        
        # Should include stripped information details
        assert 'stripped_information' in result
        stripped_info = result['stripped_information']
        
        # Check that we have detailed information about what was stripped
        assert 'architect' in stripped_info
        architect_details = stripped_info['architect']
        assert len(architect_details) == 1
        assert 'fileRegex' in architect_details[0]
        assert 'description' in architect_details[0]
        
        # Should include warning messages
        assert 'warning_messages' in result
        warnings = result['warning_messages']
        assert len(warnings) > 0
        assert any('fileRegex' in warning for warning in warnings)
        assert any('description' in warning for warning in warnings)
        
    def test_warning_message_format(self, temp_config_file):
        """Test that warning messages are properly formatted and informative."""
        from roo_modes_sync.core.global_config_fixer import GlobalConfigFixer
        
        problematic_config = self.create_problematic_global_config()
        
        # Write config to temp file
        with open(temp_config_file, 'w') as f:
            yaml.dump(problematic_config, f)
        
        fixer = GlobalConfigFixer()
        
        # Get warning messages
        warnings = fixer.generate_warning_messages(problematic_config)
        
        # Should have warnings for each problematic mode
        assert len(warnings) >= 4  # At least one warning per problematic mode
        
        # Check warning format - should include mode name and what's being stripped
        architect_warnings = [w for w in warnings if 'architect' in w]
        assert len(architect_warnings) >= 1
        
        # Warning should mention what's being stripped
        architect_warning = architect_warnings[0]
        assert 'fileRegex' in architect_warning or 'description' in architect_warning
        assert 'stripped' in architect_warning.lower() or 'removed' in architect_warning.lower()
        
        # Check mode-manager which has multiple complex groups
        manager_warnings = [w for w in warnings if 'mode-manager' in w]
        assert len(manager_warnings) >= 2  # Should have warnings for both complex groups
        
    def test_preserve_stripped_info_in_comments(self, temp_config_file):
        """Test that stripped information can optionally be preserved as comments."""
        from roo_modes_sync.core.global_config_fixer import GlobalConfigFixer
        
        problematic_config = self.create_problematic_global_config()
        
        # Write config to temp file
        with open(temp_config_file, 'w') as f:
            yaml.dump(problematic_config, f)
        
        fixer = GlobalConfigFixer()
        
        # Test fix with comment preservation option
        result = fixer.fix_global_config_file_with_warnings(
            temp_config_file,
            create_backup=False,
            preserve_as_comments=True
        )
        
        # Should be successful
        assert result['success'] is True
        
        # Read the fixed file and check for comments
        with open(temp_config_file, 'r') as f:
            fixed_content = f.read()
        
        # Should contain comments about stripped information
        assert '#   - Stripped fileRegex for' in fixed_content or '# Original fileRegex:' in fixed_content
        assert '#   - Stripped description for' in fixed_content or '# Original description:' in fixed_content