"""Test cases for mode validation functionality."""

import pytest
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from roo_modes_sync.core.validation import (
    ModeValidator, 
    ValidationLevel, 
    ValidationResult,
    ModeValidationError
)


class TestModeValidator:
    """Test cases for ModeValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return ModeValidator()
    
    @pytest.fixture
    def temp_mode_file(self, tmp_path):
        """Create a temporary directory and file for test mode files."""
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        mode_file = modes_dir / "test-mode.yaml"
        return mode_file
    
    def create_valid_config(self) -> Dict[str, Any]:
        """Helper to create a valid mode configuration."""
        return {
            'slug': 'test-mode',
            'name': 'Test Mode',
            'roleDefinition': 'This is a test mode',
            'groups': ['read', 'edit']
        }
        
    def create_config_with_missing_field(self, field_to_remove: str) -> Dict[str, Any]:
        """Helper to create a config with a missing required field."""
        config = self.create_valid_config()
        del config[field_to_remove]
        return config
    
    def test_validation_result_init(self):
        """Test ValidationResult initialization and methods."""
        # Test init without warnings
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert result.warnings == []
        
        # Test init with warnings
        warnings = [{'level': 'warning', 'message': 'Test warning'}]
        result = ValidationResult(valid=True, warnings=warnings)
        assert result.valid is True
        assert result.warnings == warnings
        
        # Test add_warning method
        result.add_warning("New warning", "info")
        assert len(result.warnings) == 2
        assert result.warnings[-1] == {'level': 'info', 'message': 'New warning'}
        
        # Test string representation
        assert str(result) == "ValidationResult(valid=True, 2 warnings)"
    
    def test_validate_valid_config(self, validator, temp_mode_file):
        """Test validation of a valid configuration."""
        config = self.create_valid_config()
        
        # Test with collect_warnings=False (returns boolean)
        result = validator.validate_mode_config(config, temp_mode_file.name)
        assert result is True
        
        # Test with collect_warnings=True (returns ValidationResult)
        result = validator.validate_mode_config(config, temp_mode_file.name, collect_warnings=True)
        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert len(result.warnings) == 0
    
    def test_validate_missing_required_fields(self, validator, temp_mode_file):
        """Test validation fails with missing required fields."""
        required_fields = ['slug', 'name', 'roleDefinition', 'groups']
        
        for field in required_fields:
            config = self.create_config_with_missing_field(field)
            
            # Test with collect_warnings=False (should raise exception)
            with pytest.raises(ModeValidationError) as e:
                validator.validate_mode_config(config, temp_mode_file.name)
            assert f"Missing required fields" in str(e.value)
            assert field in str(e.value)
            
            # Test with collect_warnings=True (should return invalid result with warnings)
            result = validator.validate_mode_config(config, temp_mode_file.name, collect_warnings=True)
            assert result.valid is False
            assert len(result.warnings) == 1
            assert result.warnings[0]['level'] == 'error'
            assert field in result.warnings[0]['message']
    
    def test_validate_unexpected_fields(self, validator, temp_mode_file):
        """Test validation with unexpected top-level fields."""
        config = self.create_valid_config()
        config['unexpectedField'] = "Some value"
        
        # Test with NORMAL validation level (default)
        result = validator.validate_mode_config(config, temp_mode_file.name, collect_warnings=True)
        assert result.valid is True
        assert len(result.warnings) == 1
        assert "unexpectedField" in result.warnings[0]['message']
        
        # Test with STRICT validation level
        validator.set_validation_level(ValidationLevel.STRICT)
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "unexpectedField" in str(e.value)
        
        # Test with PERMISSIVE validation level
        validator.set_validation_level(ValidationLevel.PERMISSIVE)
        result = validator.validate_mode_config(config, temp_mode_file.name, collect_warnings=True)
        assert result.valid is True
        assert len(result.warnings) == 1
    
    def test_validate_string_fields(self, validator, temp_mode_file):
        """Test validation of string fields."""
        string_fields = ['slug', 'name', 'roleDefinition', 'whenToUse', 'customInstructions']
        
        for field in string_fields:
            # Test with non-string value
            config = self.create_valid_config()
            if field not in config:  # Add optional fields if needed
                config[field] = "Valid string"
            config[field] = 42  # Not a string
            
            with pytest.raises(ModeValidationError) as e:
                validator.validate_mode_config(config, temp_mode_file.name)
            assert f"must be a string" in str(e.value)
            
            # Test with empty string
            config = self.create_valid_config()
            if field not in config:  # Add optional fields if needed
                config[field] = "Valid string"
            config[field] = ""
            
            with pytest.raises(ModeValidationError) as e:
                validator.validate_mode_config(config, temp_mode_file.name)
            assert f"cannot be empty" in str(e.value)
    
    def test_validate_slug_format(self, validator, temp_mode_file):
        """Test validation of slug format."""
        # Test valid slug formats
        valid_slugs = ['test-mode', 'code', 'architect-plus', 'test-123']
        for slug in valid_slugs:
            config = self.create_valid_config()
            config['slug'] = slug
            result = validator.validate_mode_config(config, temp_mode_file.name)
            assert result is True
        
        # Test invalid slug formats
        invalid_slugs = ['Test_Mode', 'code space', 'test_underscore', 'Test', '-leading-hyphen']
        
        for slug in invalid_slugs:
            config = self.create_valid_config()
            config['slug'] = slug
            
            # With NORMAL validation (default)
            with pytest.raises(ModeValidationError) as e:
                validator.validate_mode_config(config, temp_mode_file.name)
            assert "Invalid slug format" in str(e.value)
            
            # With PERMISSIVE validation (should be a warning)
            validator.set_validation_level(ValidationLevel.PERMISSIVE)
            result = validator.validate_mode_config(config, temp_mode_file.name, collect_warnings=True)
            assert result.valid is True
            assert any("Invalid slug format" in w['message'] for w in result.warnings)
            
            # Reset validation level
            validator.set_validation_level(ValidationLevel.NORMAL)
    
    def test_validate_groups(self, validator, temp_mode_file):
        """Test validation of groups configuration."""
        # Test with valid simple groups
        valid_simple_groups = [['read'], ['edit'], ['browser'], ['command'], ['mcp'], ['read', 'edit'], ['read', 'command', 'mcp']]
        for groups in valid_simple_groups:
            config = self.create_valid_config()
            config['groups'] = groups
            result = validator.validate_mode_config(config, temp_mode_file.name)
            assert result is True
        
        # Test with invalid simple group
        config = self.create_valid_config()
        config['groups'] = ['invalid-group']
        
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "Invalid group name" in str(e.value)
        
        # Test with empty groups array (should always fail)
        config = self.create_valid_config()
        config['groups'] = []
        
        # Even with PERMISSIVE validation
        validator.set_validation_level(ValidationLevel.PERMISSIVE)
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "cannot be empty" in str(e.value)
        
        # Test with non-array groups
        config = self.create_valid_config()
        config['groups'] = "read"  # String instead of array
        
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "must be an array" in str(e.value)
    
    def test_validate_complex_groups(self, validator, temp_mode_file):
        """Test validation of complex groups configuration."""
        # Valid complex group
        config = self.create_valid_config()
        config['groups'] = [
            'read',
            ['edit', {'fileRegex': '\.md$', 'description': 'Edit markdown files'}]
        ]
        result = validator.validate_mode_config(config, temp_mode_file.name)
        assert result is True
        
        # Test invalid complex group (wrong length)
        config = self.create_valid_config()
        config['groups'] = [['edit', {'fileRegex': '\.md$'}, 'extra-item']]
        
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "must have exactly 2 items" in str(e.value)
        
        # Test invalid complex group (first item not 'edit')
        config = self.create_valid_config()
        config['groups'] = [['read', {'fileRegex': '\.md$'}]]
        
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "First item in complex group must be 'edit'" in str(e.value)
        
        # Test invalid complex group (second item not object)
        config = self.create_valid_config()
        config['groups'] = [['edit', 'not-an-object']]
        
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "must be an object" in str(e.value)
        
        # Test invalid complex group (missing fileRegex)
        config = self.create_valid_config()
        config['groups'] = [['edit', {'description': 'No file regex'}]]
        
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "must have 'fileRegex' property" in str(e.value)
        
        # Test invalid complex group (invalid regex)
        config = self.create_valid_config()
        config['groups'] = [['edit', {'fileRegex': '[invalid regex'}]]
        
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "Invalid regex pattern" in str(e.value)
        
        # Test unexpected properties in complex group
        config = self.create_valid_config()
        config['groups'] = [
            ['edit', {'fileRegex': '\.md$', 'unexpectedProp': 'value'}]
        ]
        
        # With NORMAL validation (should pass)
        result = validator.validate_mode_config(config, temp_mode_file.name)
        assert result is True
        
        # With STRICT validation (should fail)
        validator.set_validation_level(ValidationLevel.STRICT)
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "Unexpected properties in complex group" in str(e.value)
    
    def test_extended_schema_validation(self, validator, temp_mode_file):
        """Test validation with extended schemas."""
        # Register a test extended schema
        test_schema = {
            'properties': {
                'customInstructions': {
                    'type': 'string'
                },
                'extensions': {
                    'type': 'object',
                    'required': ['version']
                }
            }
        }
        validator.register_extended_schema('test-extension', test_schema)
        
        # Test valid config with extended schema
        config = self.create_valid_config()
        config['customInstructions'] = 'Valid instructions'
        config['extensions'] = {'version': '1.0'}
        
        result = validator.validate_mode_config(
            config, temp_mode_file.name, extensions=['test-extension']
        )
        assert result is True
        
        # Test invalid type
        config['customInstructions'] = 42  # Not a string
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(
                config, temp_mode_file.name, extensions=['test-extension']
            )
        assert "must be a string" in str(e.value)
        
        # Test missing required field
        config = self.create_valid_config()
        config['extensions'] = {}  # Missing required 'version'
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(
                config, temp_mode_file.name, extensions=['test-extension']
            )
        assert "Missing required fields" in str(e.value)
        assert "version" in str(e.value)


class TestDevelopmentMetadataHandling:
    """Test cases for development metadata handling functionality."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return ModeValidator()
    
    @pytest.fixture
    def temp_mode_file(self, tmp_path):
        """Create a temporary directory and file for test mode files."""
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        mode_file = modes_dir / "test-mode.yaml"
        return mode_file
    
    def create_valid_config_with_dev_metadata(self) -> Dict[str, Any]:
        """Helper to create a valid mode configuration with development metadata."""
        return {
            'slug': 'test-mode',
            'name': 'Test Mode',
            'roleDefinition': 'This is a test mode',
            'groups': ['read', 'edit'],
            'source': 'local',  # Development metadata
            'model': 'claude-sonnet-4'  # Development metadata
        }
    
    def test_validate_mode_with_development_metadata_should_pass(self, validator, temp_mode_file):
        """Test that mode files with development metadata validate successfully."""
        config = self.create_valid_config_with_dev_metadata()
        
        # Should validate successfully with collect_warnings=True
        result = validator.validate_mode_config(config, temp_mode_file.name, collect_warnings=True)
        assert isinstance(result, ValidationResult)
        assert result.valid is True
        
        # Should validate successfully as boolean
        result = validator.validate_mode_config(config, temp_mode_file.name)
        assert result is True
    
    def test_development_metadata_fields_are_accepted(self, validator, temp_mode_file):
        """Test that specific development metadata fields are accepted during validation."""
        config = {
            'slug': 'test-mode',
            'name': 'Test Mode',
            'roleDefinition': 'This is a test mode',
            'groups': ['read', 'edit']
        }
        
        # Test each development metadata field individually
        dev_metadata_fields = [
            ('source', 'local'),
            ('source', 'global'),
            ('model', 'claude-sonnet-4'),
            ('model', 'gpt-4'),
        ]
        
        for field_name, field_value in dev_metadata_fields:
            test_config = config.copy()
            test_config[field_name] = field_value
            
            result = validator.validate_mode_config(test_config, temp_mode_file.name, collect_warnings=True)
            assert result.valid is True, f"Validation failed for {field_name}: {field_value}"
    
    def test_strip_development_metadata_functionality(self, validator, temp_mode_file):
        """Test that development metadata can be stripped from configuration."""
        config_with_metadata = self.create_valid_config_with_dev_metadata()
        
        # Test the strip_development_metadata method (to be implemented)
        stripped_config = validator.strip_development_metadata(config_with_metadata)
        
        # Stripped config should not contain development metadata fields
        assert 'source' not in stripped_config
        assert 'model' not in stripped_config
        
        # Stripped config should retain all core Roo fields
        expected_core_fields = {'slug', 'name', 'roleDefinition', 'groups'}
        assert set(stripped_config.keys()) == expected_core_fields
        
        # Values should be unchanged
        assert stripped_config['slug'] == 'test-mode'
        assert stripped_config['name'] == 'Test Mode'
        assert stripped_config['roleDefinition'] == 'This is a test mode'
        assert stripped_config['groups'] == ['read', 'edit']
    
    def test_strip_development_metadata_preserves_optional_core_fields(self, validator, temp_mode_file):
        """Test that stripping preserves optional core Roo fields."""
        config = self.create_valid_config_with_dev_metadata()
        config['whenToUse'] = 'Use this mode for testing'
        config['customInstructions'] = 'Follow these instructions'
        
        stripped_config = validator.strip_development_metadata(config)
        
        # Should preserve optional core fields
        assert 'whenToUse' in stripped_config
        assert 'customInstructions' in stripped_config
        assert stripped_config['whenToUse'] == 'Use this mode for testing'
        assert stripped_config['customInstructions'] == 'Follow these instructions'
        
        # Should remove development metadata
        assert 'source' not in stripped_config
        assert 'model' not in stripped_config
    
    def test_mixed_valid_invalid_scenarios(self, validator, temp_mode_file):
        """Test scenarios with both valid metadata and invalid core fields."""
        # Test with development metadata but missing required core field
        config = self.create_valid_config_with_dev_metadata()
        del config['slug']  # Remove required field
        
        # Should still fail validation due to missing core field
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "Missing required fields" in str(e.value)
        assert "slug" in str(e.value)
        
        # Test with development metadata and invalid core field value
        config = self.create_valid_config_with_dev_metadata()
        config['groups'] = ['invalid-group']  # Invalid core field value
        
        # Should fail validation due to invalid core field
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(config, temp_mode_file.name)
        assert "Invalid group name" in str(e.value)
    
    def test_unknown_metadata_fields_still_generate_warnings(self, validator, temp_mode_file):
        """Test that unknown fields (not development metadata) still generate warnings."""
        config = self.create_valid_config_with_dev_metadata()
        config['unknownField'] = 'some value'  # This should still be flagged
        
        result = validator.validate_mode_config(config, temp_mode_file.name, collect_warnings=True)
        assert result.valid is True
        
        # Should have warning for unknown field but not for development metadata
        warnings_messages = [w['message'] for w in result.warnings]
        assert any('unknownField' in msg for msg in warnings_messages)
        
        # Should NOT have warnings for development metadata fields
        assert not any('source' in msg for msg in warnings_messages)
        assert not any('model' in msg for msg in warnings_messages)
    
    def test_get_development_metadata_fields(self, validator):
        """Test that development metadata fields are properly defined."""
        dev_fields = validator.get_development_metadata_fields()
        
        # Should include expected development metadata fields
        expected_fields = {'source', 'model'}
        assert set(dev_fields) == expected_fields
    
    def test_backward_compatibility_with_existing_validation(self, validator, temp_mode_file):
        """Test that existing validation behavior is preserved for core fields."""
        # Test with standard config (no development metadata)
        standard_config = {
            'slug': 'test-mode',
            'name': 'Test Mode',
            'roleDefinition': 'This is a test mode',
            'groups': ['read', 'edit']
        }
        
        # Should work exactly as before
        result = validator.validate_mode_config(standard_config, temp_mode_file.name)
        assert result is True
        
        # Test with invalid standard config
        invalid_config = standard_config.copy()
        del invalid_config['slug']
        
        # Should fail exactly as before
        with pytest.raises(ModeValidationError) as e:
            validator.validate_mode_config(invalid_config, temp_mode_file.name)
        assert "Missing required fields" in str(e.value)