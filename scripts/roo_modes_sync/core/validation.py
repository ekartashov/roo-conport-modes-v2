#!/usr/bin/env python3
"""
Mode configuration validation functionality.
"""

import re
import enum
import yaml
from pathlib import Path
from typing import Dict, Any, List, Union, Optional


class ValidationLevel(enum.Enum):
    """Validation strictness levels."""
    PERMISSIVE = 1  # Allow minor issues, collect warnings
    NORMAL = 2      # Default level, balance between strictness and flexibility
    STRICT = 3      # Strict validation, reject any deviation from schema


class ValidationResult:
    """Result of a validation operation, including warnings."""
    
    def __init__(self, valid: bool, warnings: Optional[List[Dict[str, str]]] = None):
        """
        Initialize validation result.
        
        Args:
            valid: Whether validation passed
            warnings: List of warning dictionaries, each with 'level' and 'message'
        """
        self.valid = valid
        self.warnings = warnings or []
    
    def add_warning(self, message: str, level: str = "warning"):
        """
        Add a warning to the validation result.
        
        Args:
            message: Warning message
            level: Warning level ('info', 'warning', 'error')
        """
        self.warnings.append({
            'level': level,
            'message': message
        })
    
    def __str__(self):
        """String representation of validation result."""
        return f"ValidationResult(valid={self.valid}, {len(self.warnings)} warnings)"


class ModeValidationError(Exception):
    """Error raised when mode validation fails."""
    pass


class YAMLStructureError(Exception):
    """Error raised when YAML structure validation fails."""
    pass


class ModeValidator:
    """Validates mode configuration file contents."""
    
    # Define constants for validation
    REQUIRED_FIELDS = ['slug', 'name', 'roleDefinition', 'groups']
    OPTIONAL_FIELDS = ['whenToUse', 'customInstructions']
    VALID_TOP_LEVEL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS
    VALID_SIMPLE_GROUPS = ['read', 'edit', 'browser', 'command', 'mcp']
    SLUG_PATTERN = r'^[a-z0-9]+(-[a-z0-9]+)*$'
    
    # Development metadata fields that are allowed but stripped during sync
    DEVELOPMENT_METADATA_FIELDS = ['source', 'model']
    ENHANCED_VALID_TOP_LEVEL_FIELDS = VALID_TOP_LEVEL_FIELDS + DEVELOPMENT_METADATA_FIELDS
    
    def __init__(self):
        """Initialize the validator with default settings."""
        self.validation_level = ValidationLevel.NORMAL
        self.extended_schemas = {}
    
    def set_validation_level(self, level: ValidationLevel):
        """
        Set the validation strictness level.
        
        Args:
            level: Validation level (PERMISSIVE, NORMAL, or STRICT)
        """
        self.validation_level = level
    
    def register_extended_schema(self, name: str, schema: Dict[str, Any]):
        """
        Register an extended validation schema for specific extensions.
        
        Args:
            name: Name of the extension schema
            schema: Schema dictionary defining additional validation rules
        """
        self.extended_schemas[name] = schema
    
    def validate_mode_config(self, config: Dict[str, Any], filename: str, 
                            collect_warnings: bool = False,
                            extensions: Optional[List[str]] = None) -> Union[bool, ValidationResult]:
        """
        Validate a mode configuration.
        
        Args:
            config: Mode configuration dictionary
            filename: Source filename (for error messages)
            collect_warnings: If True, return ValidationResult with warnings
            extensions: List of extension schemas to apply
            
        Returns:
            If collect_warnings is False: True if valid
            If collect_warnings is True: ValidationResult object
            
        Raises:
            ModeValidationError: If validation fails
        """
        result = ValidationResult(valid=True)
        validation_errors = []
        
        # Check for required fields (always strict)
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in config]
        if missing_fields:
            error_msg = f"Missing required fields in {filename}: {', '.join(missing_fields)}"
            if collect_warnings:
                result.valid = False
                result.add_warning(error_msg, "error")
                return result
            else:
                raise ModeValidationError(error_msg)
        
        # Check for unexpected top-level properties (using enhanced list that includes dev metadata)
        unexpected_fields = [field for field in config if field not in self.ENHANCED_VALID_TOP_LEVEL_FIELDS]
        if unexpected_fields:
            error_msg = f"Unexpected properties in {filename}: {', '.join(unexpected_fields)}"
            if self.validation_level == ValidationLevel.STRICT:
                validation_errors.append(error_msg)
            else:
                # For non-strict levels, this is a warning
                result.add_warning(error_msg)
        
        # Validate string fields are strings and not empty
        for field in ['slug', 'name', 'roleDefinition']:
            try:
                self._validate_string_field(config, field, filename)
            except ModeValidationError as e:
                validation_errors.append(str(e))
        
        # Validate optional string fields if present
        for field in ['whenToUse', 'customInstructions']:
            if field in config:
                try:
                    self._validate_string_field(config, field, filename)
                except ModeValidationError as e:
                    validation_errors.append(str(e))
        
        # Validate slug format
        if 'slug' in config and isinstance(config['slug'], str):
            if not re.match(self.SLUG_PATTERN, config['slug']):
                error_msg = (
                    f"Invalid slug format in {filename}: {config['slug']}. "
                    f"Slugs must be lowercase alphanumeric with hyphens."
                )
                
                if self.validation_level == ValidationLevel.PERMISSIVE:
                    result.add_warning(error_msg)
                else:
                    validation_errors.append(error_msg)
        
        # Validate groups
        if 'groups' in config:
            # First check if groups is an array
            if not isinstance(config['groups'], list):
                error_msg = f"Field 'groups' in {filename} must be an array"
                if collect_warnings:
                    result.valid = False
                    result.add_warning(error_msg, "error")
                else:
                    raise ModeValidationError(error_msg)
            else:
                try:
                    self._validate_groups(config['groups'], filename)
                except ModeValidationError as e:
                    if (self.validation_level == ValidationLevel.PERMISSIVE and
                        'cannot be empty' not in str(e)):  # Empty groups always invalid
                        result.add_warning(str(e))
                    else:
                        validation_errors.append(str(e))
        
        # Apply extended schemas if specified
        if extensions:
            for extension in extensions:
                if extension in self.extended_schemas:
                    schema = self.extended_schemas[extension]
                    try:
                        self._validate_against_extended_schema(config, schema, filename)
                    except ModeValidationError as e:
                        validation_errors.append(str(e))
        
        # If there are validation errors, raise exception or add to result
        if validation_errors:
            error_msg = "\n".join(validation_errors)
            if collect_warnings:
                result.valid = False
                for error in validation_errors:
                    result.add_warning(error, "error")
            else:
                raise ModeValidationError(error_msg)
        
        # Return appropriate result
        if collect_warnings:
            return result
        else:
            return True
    
    def _validate_string_field(self, config: Dict[str, Any], field: str, filename: str) -> None:
        """
        Validate that a field is a non-empty string.
        
        Args:
            config: Mode configuration dictionary
            field: Field name to validate
            filename: Source filename (for error messages)
        
        Raises:
            ModeValidationError: If validation fails
        """
        value = config.get(field)
        
        if not isinstance(value, str):
            raise ModeValidationError(
                f"Field '{field}' in {filename} must be a string, got {type(value).__name__}"
            )
        
        if value == "":
            raise ModeValidationError(f"Field '{field}' in {filename} cannot be empty")
    
    def _validate_groups(self, groups: List, filename: str) -> None:
        """
        Validate groups configuration.
        
        Args:
            groups: Groups configuration (must be a list)
            filename: Source filename (for error messages)
            
        Raises:
            ModeValidationError: If validation fails
        """
        
        if not groups:
            raise ModeValidationError(f"Groups array in {filename} cannot be empty")
        
        # Validate each group item
        for group_item in groups:
            if isinstance(group_item, str):
                self._validate_simple_group(group_item, filename)
            elif isinstance(group_item, list):
                self._validate_complex_group_array(group_item, filename)
            elif isinstance(group_item, dict):
                self._validate_complex_group_object(group_item, filename)
            else:
                raise ModeValidationError(
                    f"Invalid group item in {filename}: {group_item}. "
                    f"Must be a string, array, or object."
                )
    
    def _validate_simple_group(self, group_name: str, filename: str) -> None:
        """
        Validate a simple group name.
        
        Args:
            group_name: Group name to validate
            filename: Source filename (for error messages)
            
        Raises:
            ModeValidationError: If validation fails
        """
        if group_name not in self.VALID_SIMPLE_GROUPS:
            raise ModeValidationError(
                f"Invalid group name in {filename}: '{group_name}'. "
                f"Valid simple groups are: {', '.join(self.VALID_SIMPLE_GROUPS)}"
            )
    
    def _validate_complex_group_array(self, complex_group: List, filename: str) -> None:
        """
        Validate a complex group configuration.
        
        Args:
            complex_group: Complex group configuration array
            filename: Source filename (for error messages)
            
        Raises:
            ModeValidationError: If validation fails
        """
        # Must have exactly 2 items
        if len(complex_group) != 2:
            raise ModeValidationError(
                f"Complex group in {filename} must have exactly 2 items, got {len(complex_group)}"
            )
        
        # First item must be 'edit'
        if complex_group[0] != 'edit':
            raise ModeValidationError(
                f"First item in complex group must be 'edit', got '{complex_group[0]}'"
            )
        
        # Second item must be an object
        if not isinstance(complex_group[1], dict):
            raise ModeValidationError(
                f"Second item in complex group must be an object, got {type(complex_group[1]).__name__}"
            )
        
        # Must have fileRegex property
        config_obj = complex_group[1]
        if 'fileRegex' not in config_obj:
            raise ModeValidationError(
                f"Complex group config must have 'fileRegex' property in {filename}"
            )
        
        # fileRegex must be a valid regex
        file_regex = config_obj['fileRegex']
        if not isinstance(file_regex, str):
            raise ModeValidationError(
                f"'fileRegex' must be a string in {filename}, got {type(file_regex).__name__}"
            )
        
        # Check that the regex is valid
        try:
            re.compile(file_regex)
        except re.error:
            raise ModeValidationError(
                f"Invalid regex pattern '{file_regex}' in {filename}"
            )
        
        # Check for unexpected properties
        valid_config_props = ['fileRegex', 'description']
        unexpected_props = [prop for prop in config_obj if prop not in valid_config_props]
        if unexpected_props:
            if self.validation_level == ValidationLevel.STRICT:
                raise ModeValidationError(
                    f"Unexpected properties in complex group config in {filename}: "
                    f"{', '.join(unexpected_props)}"
                )
            # Otherwise, we'll let it pass (NORMAL or PERMISSIVE levels)
    
    def _validate_complex_group_object(self, complex_group: Dict, filename: str) -> None:
        """
        Validate a complex group configuration using the new object syntax.
        
        This validates the correct YAML structure: {edit: {fileRegex: ..., description: ...}}
        
        Args:
            complex_group: Complex group configuration object
            filename: Source filename (for error messages)
            
        Raises:
            ModeValidationError: If validation fails
        """
        # Must have exactly one key
        if len(complex_group) != 1:
            raise ModeValidationError(
                f"Complex group in {filename} must have exactly one key, got {len(complex_group)} keys: {list(complex_group.keys())}"
            )
        
        # Get the group name (the key) and config (the value)
        group_name = list(complex_group.keys())[0]
        group_config = complex_group[group_name]
        
        # Group name must be valid
        if group_name not in self.VALID_SIMPLE_GROUPS:
            raise ModeValidationError(
                f"Invalid group name '{group_name}' in complex group in {filename}. "
                f"Valid group names are: {', '.join(self.VALID_SIMPLE_GROUPS)}"
            )
        
        # Group config must be an object
        if not isinstance(group_config, dict):
            raise ModeValidationError(
                f"Complex group config for '{group_name}' must be an object in {filename}, got {type(group_config).__name__}"
            )
        
        # Must have fileRegex property
        if 'fileRegex' not in group_config:
            raise ModeValidationError(
                f"Complex group config for '{group_name}' must have 'fileRegex' property in {filename}"
            )
        
        # fileRegex must be a valid regex string
        file_regex = group_config['fileRegex']
        if not isinstance(file_regex, str):
            raise ModeValidationError(
                f"'fileRegex' must be a string in {filename}, got {type(file_regex).__name__}"
            )
        
        # Check that the regex is valid
        try:
            re.compile(file_regex)
        except re.error:
            raise ModeValidationError(
                f"Invalid regex pattern '{file_regex}' in {filename}"
            )
        
        # Check for unexpected properties
        valid_config_props = ['fileRegex', 'description']
        unexpected_props = [prop for prop in group_config if prop not in valid_config_props]
        if unexpected_props:
            if self.validation_level == ValidationLevel.STRICT:
                raise ModeValidationError(
                    f"Unexpected properties in complex group config for '{group_name}' in {filename}: "
                    f"{', '.join(unexpected_props)}"
                )
            # Otherwise, we'll let it pass (NORMAL or PERMISSIVE levels)
    
    def _validate_against_extended_schema(self, config: Dict[str, Any], schema: Dict[str, Any], filename: str) -> None:
        """
        Validate a config against an extended schema.
        
        Args:
            config: Mode configuration dictionary
            schema: Extended schema dictionary
            filename: Source filename (for error messages)
            
        Raises:
            ModeValidationError: If validation fails
        """
        # Simple implementation - can be expanded with a full JSON Schema validator
        if 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                # Check if the property is present
                if prop_name in config:
                    # Check type
                    if 'type' in prop_schema:
                        expected_type = prop_schema['type']
                        if expected_type == 'object' and not isinstance(config[prop_name], dict):
                            raise ModeValidationError(
                                f"Property '{prop_name}' in {filename} must be an object"
                            )
                        elif expected_type == 'array' and not isinstance(config[prop_name], list):
                            raise ModeValidationError(
                                f"Property '{prop_name}' in {filename} must be an array"
                            )
                        elif expected_type == 'string' and not isinstance(config[prop_name], str):
                            raise ModeValidationError(
                                f"Property '{prop_name}' in {filename} must be a string"
                            )
                    
                    # Check required sub-properties for objects
                    if isinstance(config[prop_name], dict) and 'required' in prop_schema:
                        obj = config[prop_name]
                        missing = [field for field in prop_schema['required'] if field not in obj]
                        if missing:
                            raise ModeValidationError(
                                f"Missing required fields in '{prop_name}' in {filename}: {', '.join(missing)}"
                            )
    
    def get_development_metadata_fields(self) -> List[str]:
        """
        Get the list of development metadata fields that are allowed but stripped during sync.
        
        Returns:
            List of development metadata field names
        """
        return self.DEVELOPMENT_METADATA_FIELDS.copy()
    
    def strip_development_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strip development metadata fields from a configuration, returning a clean Roo-compatible config.
        
        Args:
            config: Mode configuration dictionary (potentially containing development metadata)
            
        Returns:
            Configuration dictionary with development metadata fields removed
        """
        stripped_config = {}
        
        for key, value in config.items():
            if key not in self.DEVELOPMENT_METADATA_FIELDS:
                stripped_config[key] = value
        
        return stripped_config
    
    def validate_yaml_structure(self, file_path: str, collect_warnings: bool = False) -> Union[bool, ValidationResult]:
        """
        Validate the YAML structure of a mode file, specifically checking for malformed groups.
        
        This method checks for YAML parsing errors and structural issues like double-nested
        arrays in the groups section that cause the malformed YAML we've encountered.
        
        Args:
            file_path: Path to the YAML file to validate
            collect_warnings: If True, return ValidationResult with warnings
            
        Returns:
            If collect_warnings is False: True if valid
            If collect_warnings is True: ValidationResult object
            
        Raises:
            YAMLStructureError: If YAML structure validation fails
        """
        result = ValidationResult(valid=True)
        
        try:
            # Check if file exists
            if not Path(file_path).exists():
                error_msg = f"File not found: {file_path}"
                if collect_warnings:
                    result.valid = False
                    result.add_warning(error_msg, "error")
                    return result
                else:
                    raise YAMLStructureError(error_msg)
            
            # Read and parse YAML
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Check for empty content
            if not content:
                error_msg = f"YAML file is empty: {file_path}"
                if collect_warnings:
                    result.valid = False
                    result.add_warning(error_msg, "error")
                    return result
                else:
                    raise YAMLStructureError(error_msg)
            
            # Parse YAML
            try:
                parsed_yaml = yaml.safe_load(content)
            except yaml.YAMLError as e:
                error_msg = f"YAML parsing error in {file_path}: {str(e)}"
                if collect_warnings:
                    result.valid = False
                    result.add_warning(error_msg, "error")
                    return result
                else:
                    raise YAMLStructureError(error_msg)
            
            # Check if parsed content is a dictionary
            if not isinstance(parsed_yaml, dict):
                error_msg = f"YAML content must be a dictionary in {file_path}"
                if collect_warnings:
                    result.valid = False
                    result.add_warning(error_msg, "error")
                    return result
                else:
                    raise YAMLStructureError(error_msg)
            
            # Check for malformed groups structure if groups exist
            if 'groups' in parsed_yaml and isinstance(parsed_yaml['groups'], list):
                groups_issues = self._detect_malformed_groups_structure(parsed_yaml['groups'])
                if groups_issues:
                    error_msg = f"Malformed groups structure in {file_path}: {'; '.join(groups_issues)}"
                    if collect_warnings:
                        result.valid = False
                        result.add_warning(error_msg, "error")
                        return result
                    else:
                        raise YAMLStructureError(error_msg)
            
            # If we get here, YAML structure is valid
            if collect_warnings:
                return result
            else:
                return True
                
        except (IOError, OSError) as e:
            error_msg = f"Error reading file {file_path}: {str(e)}"
            if collect_warnings:
                result.valid = False
                result.add_warning(error_msg, "error")
                return result
            else:
                raise YAMLStructureError(error_msg)
    
    def _detect_malformed_groups_structure(self, groups: List[Any]) -> List[str]:
        """
        Detect malformed groups structure, specifically double-nested arrays.
        
        This method identifies the specific YAML formatting issues we've encountered:
        - Double-nested arrays like `- - edit` instead of `- edit:`
        - Complex group arrays that should be objects
        
        Args:
            groups: The groups list from parsed YAML
            
        Returns:
            List of issue descriptions (empty if no issues found)
        """
        issues = []
        
        for i, group_item in enumerate(groups):
            # Check for double-nested arrays (the main issue we're fixing)
            if isinstance(group_item, list):
                # This is the problematic structure: a list within the groups list
                # Examples: `- - edit`, `- - command`
                issues.append(
                    f"Double-nested array at groups[{i}]: {group_item}. "
                    f"Should be a simple string like 'edit' or a complex object like "
                    f"'{{'edit': {{'fileRegex': '...'}}}}'"
                )
            
            # Additional check: if it's a dict, ensure it follows proper complex group format
            elif isinstance(group_item, dict):
                # Complex groups should have exactly one key that is a valid group name
                if len(group_item) != 1:
                    issues.append(
                        f"Complex group at groups[{i}] should have exactly one key: {group_item}"
                    )
                else:
                    group_name = list(group_item.keys())[0]
                    if group_name not in self.VALID_SIMPLE_GROUPS:
                        issues.append(
                            f"Invalid group name '{group_name}' in complex group at groups[{i}]"
                        )
            
            # Simple string groups are always valid (we validate the names elsewhere)
            elif isinstance(group_item, str):
                continue
            
            # Any other type is invalid
            else:
                issues.append(
                    f"Invalid group item type at groups[{i}]: {type(group_item).__name__}. "
                    f"Must be string, list array (for complex groups), or object."
                )
        
        return issues
    
    def validate_mode_file(self, file_path: str, collect_warnings: bool = False,
                          extensions: Optional[List[str]] = None) -> Union[bool, ValidationResult]:
        """
        Validate a complete mode file, including both YAML structure and mode configuration.
        
        This method first validates the YAML structure, then validates the mode configuration.
        
        Args:
            file_path: Path to the mode file to validate
            collect_warnings: If True, return ValidationResult with warnings
            extensions: List of extension schemas to apply
            
        Returns:
            If collect_warnings is False: True if valid
            If collect_warnings is True: ValidationResult object
            
        Raises:
            YAMLStructureError: If YAML structure validation fails
            ModeValidationError: If mode configuration validation fails
        """
        # First validate YAML structure
        yaml_result = self.validate_yaml_structure(file_path, collect_warnings=collect_warnings)
        
        if collect_warnings and isinstance(yaml_result, ValidationResult):
            if not yaml_result.valid:
                return yaml_result
        elif not yaml_result:
            # Should not reach here since validate_yaml_structure raises exception on failure
            # when collect_warnings=False, but just in case
            return False
        
        # If YAML structure is valid, load and validate mode configuration
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                parsed_yaml = yaml.safe_load(f)
            
            # Validate mode configuration
            filename = Path(file_path).name
            mode_result = self.validate_mode_config(
                parsed_yaml, filename, collect_warnings=collect_warnings, extensions=extensions
            )
            
            if collect_warnings:
                # Combine results if both use ValidationResult
                if isinstance(yaml_result, ValidationResult) and isinstance(mode_result, ValidationResult):
                    combined_result = ValidationResult(
                        valid=yaml_result.valid and mode_result.valid,
                        warnings=yaml_result.warnings + mode_result.warnings
                    )
                    return combined_result
                else:
                    return mode_result
            else:
                return mode_result
                
        except (IOError, OSError) as e:
            error_msg = f"Error reading file {file_path}: {str(e)}"
            if collect_warnings:
                result = ValidationResult(valid=False)
                result.add_warning(error_msg, "error")
                return result
            else:
                raise YAMLStructureError(error_msg)
        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error in {file_path}: {str(e)}"
            if collect_warnings:
                result = ValidationResult(valid=False)
                result.add_warning(error_msg, "error")
                return result
            else:
                raise YAMLStructureError(error_msg)