"""Test cases for YAML structure validation functionality."""

import pytest

from roo_modes_sync.core.validation import (
    ModeValidator,
    ValidationResult,
    YAMLStructureError
)


class TestYAMLStructureValidation:
    """Test cases for YAML structure validation."""
    
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
    
    def create_valid_yaml_content(self) -> str:
        """Helper to create valid YAML content string."""
        return """slug: test-mode
name: Test Mode
roleDefinition: This is a test mode
groups:
  - read
  - edit:
      fileRegex: \\.md$
      description: Documentation files (markdown files only)
  - browser
  - command
  - mcp
source: local
"""
    
    def create_malformed_groups_yaml_content(self) -> str:
        """Helper to create YAML content with malformed groups section (double-nested arrays)."""
        return """slug: test-mode
name: Test Mode
roleDefinition: This is a test mode
groups:
  - read
  - - edit
  - browser
  - command
  - mcp
source: local
"""
    
    def create_malformed_complex_groups_yaml_content(self) -> str:
        """Helper to create YAML content with malformed complex groups section."""
        return """slug: test-mode
name: Test Mode
roleDefinition: This is a test mode
groups:
  - read
  - - edit:
      fileRegex: \\.md$
      description: Documentation files
  - browser
source: local
"""
    
    def create_mixed_malformed_groups_yaml_content(self) -> str:
        """Helper to create YAML content with mixed malformed and valid groups."""
        return """slug: test-mode
name: Test Mode
roleDefinition: This is a test mode
groups:
  - read
  - - edit
  - browser
  - - command
  - mcp
source: local
"""

    def test_validate_yaml_structure_valid_file(self, validator, temp_mode_file):
        """Test that valid YAML structure passes validation."""
        # Write valid YAML content to file
        temp_mode_file.write_text(self.create_valid_yaml_content())
        
        # Should validate successfully
        result = validator.validate_yaml_structure(str(temp_mode_file))
        assert result is True
        
        # Should also work with collect_warnings=True
        result = validator.validate_yaml_structure(str(temp_mode_file), collect_warnings=True)
        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert len(result.warnings) == 0
    
    def test_validate_yaml_structure_malformed_groups(self, validator, temp_mode_file):
        """Test that malformed groups structure (double-nested arrays) fails validation."""
        # Write malformed YAML content to file
        temp_mode_file.write_text(self.create_malformed_groups_yaml_content())
        
        # Should fail validation with YAMLStructureError
        with pytest.raises(YAMLStructureError) as e:
            validator.validate_yaml_structure(str(temp_mode_file))
        
        assert "malformed groups structure" in str(e.value).lower()
        assert "double-nested array" in str(e.value).lower()
        
        # With collect_warnings=True, should return invalid result
        result = validator.validate_yaml_structure(str(temp_mode_file), collect_warnings=True)
        assert isinstance(result, ValidationResult)
        assert result.valid is False
        assert len(result.warnings) >= 1
        assert any("malformed groups" in w['message'].lower() for w in result.warnings)
    
    def test_validate_yaml_structure_malformed_complex_groups(self, validator, temp_mode_file):
        """Test that malformed complex groups structure fails validation."""
        # Write malformed complex groups YAML content to file
        temp_mode_file.write_text(self.create_malformed_complex_groups_yaml_content())
        
        # Should fail validation with YAMLStructureError
        with pytest.raises(YAMLStructureError) as e:
            validator.validate_yaml_structure(str(temp_mode_file))
        
        assert "malformed groups structure" in str(e.value).lower()
        assert "double-nested array" in str(e.value).lower()
    
    def test_validate_yaml_structure_mixed_malformed_groups(self, validator, temp_mode_file):
        """Test that mixed malformed and valid groups fails validation."""
        # Write mixed malformed YAML content to file
        temp_mode_file.write_text(self.create_mixed_malformed_groups_yaml_content())
        
        # Should fail validation and report multiple issues
        with pytest.raises(YAMLStructureError) as e:
            validator.validate_yaml_structure(str(temp_mode_file))
        
        error_message = str(e.value).lower()
        assert "malformed groups structure" in error_message
        assert "multiple" in error_message or "double-nested" in error_message
    
    def test_validate_yaml_structure_invalid_yaml_syntax(self, validator, temp_mode_file):
        """Test that completely invalid YAML syntax fails validation."""
        # Write invalid YAML syntax to file
        invalid_yaml_content = """slug: test-mode
name: Test Mode
roleDefinition: This is a test mode
groups:
  - read
  - edit: {
      fileRegex: \\.md$
      description: "Missing closing brace
  - browser
"""
        temp_mode_file.write_text(invalid_yaml_content)
        
        # Should fail with YAMLStructureError due to invalid YAML
        with pytest.raises(YAMLStructureError) as e:
            validator.validate_yaml_structure(str(temp_mode_file))
        
        assert "yaml parsing error" in str(e.value).lower() or "invalid yaml" in str(e.value).lower()
    
    def test_validate_yaml_structure_file_not_found(self, validator):
        """Test that non-existent file raises appropriate error."""
        non_existent_file = "/path/that/does/not/exist.yaml"
        
        with pytest.raises(YAMLStructureError) as e:
            validator.validate_yaml_structure(non_existent_file)
        
        assert "file not found" in str(e.value).lower() or "no such file" in str(e.value).lower()
    
    def test_detect_malformed_groups_structure_function(self, validator):
        """Test the internal _detect_malformed_groups_structure method."""
        # Test with valid groups structure
        valid_groups = [
            "read",
            {"edit": {"fileRegex": "\\.md$", "description": "Documentation files"}},
            "browser"
        ]
        issues = validator._detect_malformed_groups_structure(valid_groups)
        assert len(issues) == 0
        
        # Test with malformed groups structure (double-nested arrays)
        malformed_groups = [
            "read",
            ["edit"],  # This is the problem - should be a string or object
            "browser",
            ["command"]  # Another problem
        ]
        issues = validator._detect_malformed_groups_structure(malformed_groups)
        assert len(issues) >= 2
        assert any("double-nested array" in issue.lower() for issue in issues)
        
        # Test with mixed valid and malformed
        mixed_groups = [
            "read",
            ["edit"],  # Malformed
            {"browser": {"fileRegex": "\\.html$"}},  # Valid complex group
            "command"  # Valid simple group
        ]
        issues = validator._detect_malformed_groups_structure(mixed_groups)
        assert len(issues) == 1
        assert "double-nested array" in issues[0].lower()
    
    def test_validate_yaml_structure_integration_with_mode_validation(self, validator, temp_mode_file):
        """Test that YAML structure validation integrates with mode validation."""
        # Write malformed YAML content to file
        temp_mode_file.write_text(self.create_malformed_groups_yaml_content())
        
        # YAML structure validation should catch the issue before mode validation
        with pytest.raises(YAMLStructureError):
            validator.validate_yaml_structure(str(temp_mode_file))
        
        # If we were to parse this malformed YAML, it would create an invalid structure
        # that mode validation might not catch (depending on how YAML parser handles it)
        
    def test_validate_mode_file_with_yaml_structure_check(self, validator, temp_mode_file):
        """Test the integrated validate_mode_file method that includes YAML structure validation."""
        # Write valid YAML content
        temp_mode_file.write_text(self.create_valid_yaml_content())
        
        # Should validate successfully
        result = validator.validate_mode_file(str(temp_mode_file))
        assert result is True
        
        # Write malformed YAML content
        temp_mode_file.write_text(self.create_malformed_groups_yaml_content())
        
        # Should fail with YAMLStructureError before reaching mode validation
        with pytest.raises(YAMLStructureError):
            validator.validate_mode_file(str(temp_mode_file))
    
    def test_yaml_structure_validation_performance(self, validator, temp_mode_file):
        """Test that YAML structure validation is performant for large files."""
        # Create a large valid YAML file
        large_yaml_content = self.create_valid_yaml_content()
        large_yaml_content += "customInstructions: >\n"
        large_yaml_content += "  " + "This is a very long instruction. " * 1000 + "\n"
        
        temp_mode_file.write_text(large_yaml_content)
        
        # Should still validate successfully and quickly
        result = validator.validate_yaml_structure(str(temp_mode_file))
        assert result is True

    def test_yaml_structure_error_reporting_quality(self, validator, temp_mode_file):
        """Test that YAML structure errors provide helpful error messages."""
        # Write malformed YAML content
        temp_mode_file.write_text(self.create_malformed_groups_yaml_content())
        
        # Capture the error and verify it provides actionable information
        with pytest.raises(YAMLStructureError) as e:
            validator.validate_yaml_structure(str(temp_mode_file))
        
        error_message = str(e.value)
        
        # Should include file path
        assert str(temp_mode_file) in error_message
        
        # Should include specific issue description
        assert "groups" in error_message.lower()
        assert "double-nested" in error_message.lower() or "malformed" in error_message.lower()
        
        # Should include line information if possible
        # Note: This might require more sophisticated implementation
        
    def test_yaml_structure_validation_edge_cases(self, validator, temp_mode_file):
        """Test YAML structure validation with edge cases."""
        # Test with empty file
        temp_mode_file.write_text("")
        
        with pytest.raises(YAMLStructureError) as e:
            validator.validate_yaml_structure(str(temp_mode_file))
        assert "empty" in str(e.value).lower() or "no content" in str(e.value).lower()
        
        # Test with only whitespace
        temp_mode_file.write_text("   \n  \n   ")
        
        with pytest.raises(YAMLStructureError) as e:
            validator.validate_yaml_structure(str(temp_mode_file))
        assert "empty" in str(e.value).lower() or "no content" in str(e.value).lower()
        
        # Test with valid YAML but no groups field
        temp_mode_file.write_text("slug: test\nname: Test")
        
        # Should pass YAML structure validation (groups validation is separate)
        result = validator.validate_yaml_structure(str(temp_mode_file))
        assert result is True