#!/usr/bin/env python3
"""
Mode discovery and categorization functionality.

Provides functionality for discovering and categorizing mode YAML files:
- Dynamic file discovery from directory
- Categorization based on naming patterns
- Basic validation of mode files
- Robust path handling
"""

import re
import logging
from pathlib import Path
import yaml
from typing import Dict, List, Optional, Any

# Try relative imports first, fall back to absolute imports
try:
    from ..exceptions import DiscoveryError
except ImportError:
    # Fallback for direct script execution
    # from exceptions import DiscoveryError  # Currently unused
    pass

# Configure logging
logger = logging.getLogger(__name__)

class ModeDiscovery:
    """Handles dynamic discovery and categorization of mode files."""
    
    def __init__(self, modes_dir: Path, recursive: bool = True):
        """
        Initialize with modes directory path.
        
        Args:
            modes_dir: Path to directory containing mode YAML files
            recursive: Whether to search subdirectories recursively (default: True).
                      When True, uses rglob() to find YAML files in all subdirectories.
                      When False, uses glob() to find YAML files only in the root directory.
        """
        self.modes_dir = modes_dir
        self.recursive = recursive
        # Cache for slug-to-relative-path mapping for recursive search
        self._slug_to_path_cache = {}
        
        # Define category patterns for mode slugs
        self.category_patterns = {
            'core': [r'^(code|architect|debug|ask|orchestrator|docs)$'],
            'enhanced': [r'.*-enhanced$', r'.*-plus$'],
            'specialized': [
                r'.*-maintenance$',
                r'.*-enhancer.*$',
                r'.*-creator$',
                r'.*-auditor$'
            ]
        }
        
        logger.debug(f"Initialized ModeDiscovery with directory: {self.modes_dir}, recursive: {self.recursive}")
    
    def _get_yaml_files(self) -> List[Path]:
        """
        Get all YAML files in the modes directory.
        
        Returns:
            List of Path objects for YAML files
        """
        if not self.modes_dir.exists() or not self.modes_dir.is_dir():
            return []
            
        try:
            if self.recursive:
                # Use recursive glob to find YAML files in subdirectories
                yaml_files = list(self.modes_dir.rglob("*.yaml"))
                logger.debug(f"Found {len(yaml_files)} YAML files recursively in {self.modes_dir}")
            else:
                # Use non-recursive glob to find YAML files only in root directory
                yaml_files = list(self.modes_dir.glob("*.yaml"))
                logger.debug(f"Found {len(yaml_files)} YAML files non-recursively in {self.modes_dir}")
            
            return yaml_files
        except Exception as e:
            logger.error(f"Error accessing modes directory {self.modes_dir}: {str(e)}")
            return []
    
    def discover_all_modes(self) -> Dict[str, List[str]]:
        """
        Discover and categorize all YAML mode files.
        
        Returns:
            Dict with categories as keys and lists of mode slugs as values
        """
        categorized_modes = {
            'core': [],
            'enhanced': [],
            'specialized': [],
            'discovered': []
        }
        
        # Clear cache for fresh discovery
        self._slug_to_path_cache = {}
        
        # Get all YAML files using the appropriate search method
        yaml_files = self._get_yaml_files()
        if not yaml_files:
            if not self.modes_dir.exists():
                logger.warning(f"Modes directory does not exist: {self.modes_dir}")
            elif not self.modes_dir.is_dir():
                logger.warning(f"Modes path is not a directory: {self.modes_dir}")
            else:
                logger.info(f"No YAML files found in {self.modes_dir}")
            return categorized_modes
        
        # Process each YAML file
        for yaml_file in yaml_files:
            mode_slug = yaml_file.stem
            
            # Store the relative path from modes_dir for this slug
            try:
                relative_path = yaml_file.relative_to(self.modes_dir)
                self._slug_to_path_cache[mode_slug] = relative_path
                logger.debug(f"Cached path mapping: {mode_slug} -> {relative_path}")
            except ValueError:
                # Fallback if relative_to fails
                self._slug_to_path_cache[mode_slug] = Path(f"{mode_slug}.yaml")
                logger.warning(f"Could not compute relative path for {yaml_file}, using fallback")
            
            # Skip if not a valid YAML file that can be loaded
            if not self._is_valid_mode_file(yaml_file):
                logger.warning(f"Skipping invalid mode file: {yaml_file}")
                continue
            
            # Categorize the mode based on its slug
            category = self.categorize_mode(mode_slug)
            categorized_modes[category].append(mode_slug)
            logger.debug(f"Categorized {mode_slug} as {category}")
        
        # Sort within categories for consistency
        for category in categorized_modes:
            categorized_modes[category].sort()
        
        # Log discovery results
        total_modes = sum(len(modes) for modes in categorized_modes.values())
        logger.info(f"Discovered {total_modes} valid modes across {len(categorized_modes)} categories")
        return categorized_modes
    
    def categorize_mode(self, mode_slug: str) -> str:
        """
        Categorize a mode based on naming patterns.
        
        Args:
            mode_slug: The mode slug to categorize
            
        Returns:
            Category name ('core', 'enhanced', 'specialized', or 'discovered')
        """
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.match(pattern, mode_slug):
                    return category
        
        return 'discovered'
    
    def _is_valid_mode_file(self, yaml_file: Path) -> bool:
        """
        Check if a YAML file is a valid mode file.
        
        Args:
            yaml_file: Path to the YAML file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not yaml_file.exists() or not yaml_file.is_file():
                logger.debug(f"Mode file does not exist or is not a file: {yaml_file}")
                return False
                
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # Check if config is None or not a dictionary
            if config is None or not isinstance(config, dict):
                logger.debug(f"Mode file has invalid YAML structure: {yaml_file}")
                return False
                
            # Basic validation - must have required fields
            required_fields = ['slug', 'name', 'roleDefinition', 'groups']
            
            for field in required_fields:
                if field not in config:
                    logger.debug(f"Mode file missing required field '{field}': {yaml_file}")
                    return False
                    
            # Additional validation for groups field
            if not isinstance(config['groups'], list) or not config['groups']:
                logger.debug(f"Mode file has invalid 'groups' field: {yaml_file}")
                return False
                
            return True
            
        except yaml.YAMLError as e:
            logger.debug(f"YAML parsing error in {yaml_file}: {str(e)}")
            return False
        except (FileNotFoundError, PermissionError) as e:
            logger.debug(f"File access error for {yaml_file}: {str(e)}")
            return False
        except Exception as e:
            logger.debug(f"Unexpected error validating {yaml_file}: {str(e)}")
            return False

    def get_mode_count(self) -> int:
        """
        Get the total number of valid modes.
        
        Returns:
            Count of valid mode files
        """
        modes = self.discover_all_modes()
        return sum(len(category_modes) for category_modes in modes.values())
    
    def get_category_info(self) -> Dict[str, Dict[str, str]]:
        """
        Get information about mode categories.
        
        Returns:
            Dictionary with category information
        """
        return {
            'core': {
                'icon': '🏗️',
                'name': 'Core Workflow',
                'description': 'Fundamental development operations'
            },
            'enhanced': {
                'icon': '💻+',
                'name': 'Enhanced Variants',
                'description': 'Extended functionality variants'
            },
            'specialized': {
                'icon': '🔧',
                'name': 'Specialized Tools',
                'description': 'Specific utilities and tools'
            },
            'discovered': {
                'icon': '📋',
                'name': 'Discovered',
                'description': 'Additional modes found'
            }
        }
        
    def find_mode_by_name(self, name: str) -> Optional[str]:
        """
        Find a mode slug by its display name (case-insensitive partial match).
        
        Args:
            name: The display name to search for
            
        Returns:
            Mode slug if found, None otherwise
        """
        if not self.modes_dir.exists() or not self.modes_dir.is_dir():
            return None
            
        name_lower = name.lower()
        
        for yaml_file in self.modes_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                if (config and isinstance(config, dict) and 
                    'name' in config and isinstance(config['name'], str) and
                    name_lower in config['name'].lower()):
                    return yaml_file.stem
                    
            except Exception:
                # Skip files with errors
                continue
                
        return None
        
    def get_mode_relative_path(self, mode_slug: str) -> Optional[Path]:
        """
        Get the relative path for a mode slug from the cached mapping.
        
        Args:
            mode_slug: The mode slug to get the path for
            
        Returns:
            Path relative to modes_dir if found, None otherwise
        """
        return self._slug_to_path_cache.get(mode_slug)
    
    def get_mode_info(self, mode_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific mode.
        
        Args:
            mode_slug: The mode slug to get information for
            
        Returns:
            Dictionary with mode information if found, None otherwise
        """
        # Try to use cached path first, fallback to simple path construction
        relative_path = self.get_mode_relative_path(mode_slug)
        if relative_path:
            mode_file = self.modes_dir / relative_path
        else:
            mode_file = self.modes_dir / f"{mode_slug}.yaml"
        
        if not mode_file.exists() or not mode_file.is_file():
            return None
            
        try:
            with open(mode_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if not self._is_valid_mode_file(mode_file):
                return None
                
            category = self.categorize_mode(mode_slug)
            
            # Add category to the mode info
            info = {
                'slug': mode_slug,
                'name': config.get('name', ''),
                'category': category,
                'roleDefinition': config.get('roleDefinition', ''),
                'whenToUse': config.get('whenToUse', ''),
                'groups': config.get('groups', [])
            }
            
            return info
            
        except Exception:
            return None