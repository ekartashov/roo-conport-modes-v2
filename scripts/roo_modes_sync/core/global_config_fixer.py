#!/usr/bin/env python3
"""
Global Roo configuration group structure fixer.

This module provides functionality to fix complex group structures in global Roo
configuration files that are not compatible with Roo's expected format.
"""

import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class GlobalConfigFixer:
    """Fixes complex group structures in global Roo configuration files."""
    
    def __init__(self):
        """Initialize the global config fixer."""
        pass
    
    def identify_problematic_modes(self, config_data: Dict[str, Any]) -> List[str]:
        """
        Identify modes that have complex group structures with fileRegex/description.
        
        Args:
            config_data: Global configuration dictionary with customModes array
            
        Returns:
            List of mode slugs that have problematic group structures
        """
        problematic_modes = []
        
        # Handle the actual global config structure with customModes array
        custom_modes = config_data.get('customModes', [])
        if not isinstance(custom_modes, list):
            return problematic_modes
        
        for mode_config in custom_modes:
            if not isinstance(mode_config, dict) or 'groups' not in mode_config:
                continue
                
            mode_slug = mode_config.get('slug', 'unknown')
            groups = mode_config['groups']
            if not isinstance(groups, list):
                continue
                
            has_complex_groups = False
            for group in groups:
                if isinstance(group, dict):
                    # Check if it has the problematic fileRegex/description structure
                    for group_name, group_config in group.items():
                        if isinstance(group_config, dict) and (
                            'fileRegex' in group_config or 'description' in group_config
                        ):
                            has_complex_groups = True
                            break
                if has_complex_groups:
                    break
            
            if has_complex_groups and mode_slug not in problematic_modes:
                problematic_modes.append(mode_slug)
                
        return problematic_modes
    
    def get_stripped_information_details(self, config_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract detailed information about what will be stripped from complex groups.
        
        Args:
            config_data: Global configuration dictionary
            
        Returns:
            Dictionary mapping mode slugs to lists of stripped information details
        """
        stripped_info = {}
        
        # Handle the actual global config structure with customModes array
        custom_modes = config_data.get('customModes', [])
        if not isinstance(custom_modes, list):
            return stripped_info
        
        for mode_config in custom_modes:
            if not isinstance(mode_config, dict) or 'groups' not in mode_config:
                continue
                
            mode_slug = mode_config.get('slug', 'unknown')
            groups = mode_config['groups']
            if not isinstance(groups, list):
                continue
                
            mode_stripped_info = []
            
            for group in groups:
                if isinstance(group, dict):
                    # Extract complex group information
                    for group_name, group_config in group.items():
                        if isinstance(group_config, dict) and (
                            'fileRegex' in group_config or 'description' in group_config
                        ):
                            stripped_detail = {
                                'group_name': group_name,
                                'fileRegex': group_config.get('fileRegex'),
                                'description': group_config.get('description')
                            }
                            mode_stripped_info.append(stripped_detail)
            
            if mode_stripped_info:
                stripped_info[mode_slug] = mode_stripped_info
                
        return stripped_info
    
    def generate_warning_messages(self, config_data: Dict[str, Any]) -> List[str]:
        """
        Generate human-readable warning messages about information that will be stripped.
        
        Args:
            config_data: Global configuration dictionary
            
        Returns:
            List of warning messages
        """
        warnings = []
        stripped_info = self.get_stripped_information_details(config_data)
        
        for mode_slug, mode_details in stripped_info.items():
            for detail in mode_details:
                group_name = detail['group_name']
                file_regex = detail.get('fileRegex')
                description = detail.get('description')
                
                warning_parts = [f"Mode '{mode_slug}' group '{group_name}':"]
                
                if file_regex:
                    warning_parts.append(f"fileRegex '{file_regex}' will be stripped")
                if description:
                    warning_parts.append(f"description '{description}' will be stripped")
                
                warnings.append(" ".join(warning_parts))
        
        return warnings
    
    def fix_complex_groups(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert complex group structures to simple group structures.
        
        This removes fileRegex and description fields from groups and converts
        them to simple string arrays as expected by Roo.
        
        Args:
            config_data: Global configuration dictionary
            
        Returns:
            Fixed configuration dictionary with simple group structures
        """
        fixed_config = config_data.copy()
        
        # Handle the actual global config structure with customModes array
        custom_modes = config_data.get('customModes', [])
        if not isinstance(custom_modes, list):
            return fixed_config
        
        fixed_custom_modes = []
        
        for mode_config in custom_modes:
            fixed_mode_config = mode_config.copy()
            
            if 'groups' in mode_config and isinstance(mode_config['groups'], list):
                groups = mode_config['groups']
                fixed_groups = []
                seen_groups = set()
                
                for group in groups:
                    if isinstance(group, str):
                        # Simple group - keep as is, but avoid duplicates
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
                        if group not in seen_groups:
                            fixed_groups.append(group)
                            seen_groups.add(str(group))
                
                fixed_mode_config['groups'] = fixed_groups
            
            fixed_custom_modes.append(fixed_mode_config)
        
        fixed_config['customModes'] = fixed_custom_modes
        return fixed_config
    
    def backup_config_file(self, config_path: Path) -> Path:
        """
        Create a backup of the configuration file with timestamp.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Path to the backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config_path.with_suffix(f".backup_{timestamp}{config_path.suffix}")
        shutil.copy2(config_path, backup_path)
        return backup_path
    
    def load_global_config(self, config_path: Path) -> Dict[str, Any]:
        """
        Load global configuration from YAML file.
        
        Args:
            config_path: Path to the global configuration file
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Global config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def save_global_config(self, config_data: Dict[str, Any], config_path: Path, 
                          preserve_as_comments: bool = False, 
                          stripped_info: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> None:
        """
        Save global configuration to YAML file with optional comment preservation.
        
        Args:
            config_data: Configuration dictionary
            config_path: Path to save the configuration file
            preserve_as_comments: Whether to add comments about stripped information
            stripped_info: Information about what was stripped (for comments)
        """
        if preserve_as_comments and stripped_info:
            # Create YAML with comments about stripped information
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write("# Global Roo Configuration with Complex Groups Fixed\n")
                f.write("# WARNING: The following information was stripped during fixing:\n")
                
                for mode_slug, mode_details in stripped_info.items():
                    f.write(f"# Mode '{mode_slug}':\n")
                    for detail in mode_details:
                        group_name = detail['group_name']
                        if detail.get('fileRegex'):
                            f.write(f"#   - Stripped fileRegex for '{group_name}': {detail['fileRegex']}\n")
                        if detail.get('description'):
                            f.write(f"#   - Stripped description for '{group_name}': {detail['description']}\n")
                
                f.write("\n")
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, indent=2)
        else:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, indent=2)
    
    def fix_global_config_file(self, config_path: Path, create_backup: bool = True) -> Dict[str, Any]:
        """
        Fix complex group structures in a global configuration file.
        
        Args:
            config_path: Path to the global configuration file
            create_backup: Whether to create a backup before modifying
            
        Returns:
            Dictionary with fix results:
            - 'success': bool - Whether the fix was successful
            - 'problematic_modes': List[str] - Modes that had issues
            - 'backup_path': Path - Path to backup file (if created)
            - 'message': str - Status message
        """
        try:
            # Load the current configuration
            config_data = self.load_global_config(config_path)
            
            # Identify problematic modes
            problematic_modes = self.identify_problematic_modes(config_data)
            
            if not problematic_modes:
                return {
                    'success': True,
                    'problematic_modes': [],
                    'backup_path': None,
                    'message': 'No problematic group structures found. Configuration is already correct.'
                }
            
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_path = self.backup_config_file(config_path)
            
            # Fix the configuration
            fixed_config = self.fix_complex_groups(config_data)
            
            # Save the fixed configuration
            self.save_global_config(fixed_config, config_path)
            
            return {
                'success': True,
                'problematic_modes': problematic_modes,
                'backup_path': backup_path,
                'message': f'Successfully fixed {len(problematic_modes)} modes: {", ".join(problematic_modes)}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'problematic_modes': [],
                'backup_path': None,
                'message': f'Error fixing configuration: {str(e)}'
            }
    
    def fix_global_config_file_with_warnings(self, config_path: Path, create_backup: bool = True,
                                           preserve_as_comments: bool = False) -> Dict[str, Any]:
        """
        Fix complex group structures with detailed warnings about stripped information.
        
        Args:
            config_path: Path to the global configuration file
            create_backup: Whether to create a backup before modifying
            preserve_as_comments: Whether to preserve stripped info as comments
            
        Returns:
            Dictionary with detailed fix results including warnings
        """
        try:
            # Load the current configuration
            config_data = self.load_global_config(config_path)
            
            # Identify problematic modes
            problematic_modes = self.identify_problematic_modes(config_data)
            
            if not problematic_modes:
                return {
                    'success': True,
                    'problematic_modes': [],
                    'backup_path': None,
                    'stripped_information': {},
                    'warning_messages': [],
                    'message': 'No problematic group structures found. Configuration is already correct.'
                }
            
            # Get detailed information about what will be stripped
            stripped_info = self.get_stripped_information_details(config_data)
            warning_messages = self.generate_warning_messages(config_data)
            
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_path = self.backup_config_file(config_path)
            
            # Fix the configuration
            fixed_config = self.fix_complex_groups(config_data)
            
            # Save the fixed configuration with optional comments
            self.save_global_config(fixed_config, config_path, preserve_as_comments, stripped_info)
            
            return {
                'success': True,
                'problematic_modes': problematic_modes,
                'backup_path': backup_path,
                'stripped_information': stripped_info,
                'warning_messages': warning_messages,
                'message': f'Successfully fixed {len(problematic_modes)} modes: {", ".join(problematic_modes)}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'problematic_modes': [],
                'backup_path': None,
                'stripped_information': {},
                'warning_messages': [],
                'message': f'Error fixing configuration: {str(e)}'
            }
    
    def validate_fixed_config(self, config_path: Path) -> Dict[str, Any]:
        """
        Validate that the fixed configuration has proper group structures.
        
        Args:
            config_path: Path to the configuration file to validate
            
        Returns:
            Dictionary with validation results:
            - 'valid': bool - Whether all modes have simple group structures
            - 'issues': List[str] - Any remaining issues found
            - 'message': str - Validation summary
        """
        try:
            config_data = self.load_global_config(config_path)
            issues = []
            
            # Handle the actual global config structure with customModes array
            custom_modes = config_data.get('customModes', [])
            if not isinstance(custom_modes, list):
                issues.append("Invalid configuration structure: 'customModes' should be an array")
                return {
                    'valid': False,
                    'issues': issues,
                    'message': 'Configuration structure is invalid.'
                }
            
            for mode_config in custom_modes:
                if not isinstance(mode_config, dict) or 'groups' not in mode_config:
                    continue
                    
                mode_slug = mode_config.get('slug', 'unknown')
                groups = mode_config['groups']
                if not isinstance(groups, list):
                    continue
                    
                for i, group in enumerate(groups):
                    if isinstance(group, dict):
                        # Check if it still has complex structure
                        for group_name, group_config in group.items():
                            if isinstance(group_config, dict) and (
                                'fileRegex' in group_config or 'description' in group_config
                            ):
                                issues.append(
                                    f"Mode '{mode_slug}' still has complex group structure at index {i}: {group}"
                                )
            
            if not issues:
                return {
                    'valid': True,
                    'issues': [],
                    'message': 'All modes have simple group structures. Configuration is valid.'
                }
            else:
                return {
                    'valid': False,
                    'issues': issues,
                    'message': f'Found {len(issues)} remaining complex group structures.'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'issues': [f'Validation error: {str(e)}'],
                'message': f'Error validating configuration: {str(e)}'
            }