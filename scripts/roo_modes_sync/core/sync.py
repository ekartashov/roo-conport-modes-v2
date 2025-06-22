#!/usr/bin/env python3
"""
Mode synchronization functionality.

Provides functionality for synchronizing mode configurations:
- Global mode application (system-wide configuration)
- Local mode application (project-specific configuration)
- Dynamic discovery and categorization
- MCP server interface support
"""

import yaml
import shutil
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class CustomYAMLDumper(yaml.SafeDumper):
    """Custom YAML dumper with proper indentation for sequences."""
    
    def write_line_break(self, data=None):
        super().write_line_break(data)

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)  # Never indentless

# Try relative imports first, fall back to absolute imports
try:
    from ..exceptions import SyncError, ConfigurationError
    from .discovery import ModeDiscovery
    from .validation import ModeValidator, ValidationLevel, ValidationResult
    from .ordering import OrderingStrategyFactory
    from .backup import BackupManager, BackupError
    from .global_config_fixer import GlobalConfigFixer
except ImportError:
    # Fallback for direct script execution
    from exceptions import SyncError
    from discovery import ModeDiscovery
    from validation import ModeValidator, ValidationLevel
    from ordering import OrderingStrategyFactory
    from backup import BackupManager, BackupError
    from global_config_fixer import GlobalConfigFixer


# Configure logging
logger = logging.getLogger(__name__)


class ModeSync:
    """
    Main synchronization class for Roo modes configuration.
    
    Handles loading mode configurations, creating global/local configurations,
    and writing to the target config files.
    """
    
    # Default path for global modes config
    DEFAULT_GLOBAL_CONFIG_PATH = Path(os.path.expanduser(
        "~/.config/VSCodium/User/globalStorage/rooveterinaryinc.roo-cline/settings/custom_modes.yaml"
    ))
    
    # Local project configuration structure
    LOCAL_CONFIG_DIR = ".roomodes"
    LOCAL_CONFIG_FILE = "modes.yaml"
    
    # Environment variable names
    ENV_MODES_DIR = "ROO_MODES_DIR"
    ENV_CONFIG_PATH = "ROO_MODES_CONFIG"
    ENV_VALIDATION_LEVEL = "ROO_MODES_VALIDATION_LEVEL"
    
    def __init__(self, modes_dir: Optional[Path] = None, recursive: bool = True):
        """
        Initialize with modes directory path.
        
        Args:
            modes_dir: Path to directory containing mode YAML files.
                       If None, will try to use ROO_MODES_DIR environment variable.
            recursive: Whether to search for modes recursively in subdirectories (default: True).
                      This parameter is passed to ModeDiscovery for file discovery behavior.
                      When True, searches all subdirectories using rglob().
                      When False, searches only the root directory using glob().
        """
        # Get modes directory from env var if not provided
        if modes_dir is None and self.ENV_MODES_DIR in os.environ:
            modes_dir = Path(os.environ[self.ENV_MODES_DIR])
        
        # Ensure modes_dir is an absolute path
        if modes_dir is not None:
            self.modes_dir = Path(modes_dir).absolute()
        else:
            # No modes_dir provided or in env var, use current directory as fallback
            self.modes_dir = Path.cwd() / "modes"
            logger.warning(f"No modes directory specified, using default: {self.modes_dir}")
        
        self.global_config_path = None
        self.local_config_path = None
        self.discovery = ModeDiscovery(self.modes_dir, recursive=recursive)
        self.validator = ModeValidator()
        self.backup_manager = None  # Will be initialized when needed
        self.global_config_fixer = GlobalConfigFixer()  # For complex group handling
        
        # Set validation level from environment if specified
        if self.ENV_VALIDATION_LEVEL in os.environ:
            level_name = os.environ[self.ENV_VALIDATION_LEVEL].upper()
            try:
                level = ValidationLevel[level_name]
                self.validator.set_validation_level(level)
                logger.info(f"Set validation level to {level_name} from environment variable")
            except KeyError:
                logger.warning(f"Invalid validation level in environment: {level_name}")
        
        # Set config path from environment if specified
        if self.ENV_CONFIG_PATH in os.environ:
            self.set_global_config_path(Path(os.environ[self.ENV_CONFIG_PATH]))
        
        # Initialize options with defaults
        self.options = {
            "continue_on_validation_error": False,
            "collect_warnings": True,
            "validation_level": None  # Use validator's default
        }
    
    def set_options(self, options: Dict[str, Any]) -> None:
        """
        Set options for the sync operation.
        
        Args:
            options: Dictionary of options
        """
        self.options.update(options)
        
        # Apply validation level if specified
        if "validation_level" in options and options["validation_level"] is not None:
            self.validator.set_validation_level(options["validation_level"])
        
    def set_global_config_path(self, config_path: Optional[Path] = None) -> None:
        """
        Set the path for the global configuration file.
        
        Args:
            config_path: Path to the global config file or None to use default
        """
        if config_path is None:
            # Try environment variable first
            if self.ENV_CONFIG_PATH in os.environ:
                config_path = Path(os.environ[self.ENV_CONFIG_PATH])
            else:
                config_path = self.DEFAULT_GLOBAL_CONFIG_PATH
        
        # Ensure path is absolute
        self.global_config_path = Path(config_path).absolute()
        self.local_config_path = None  # Reset local path
        logger.debug(f"Set global config path: {self.global_config_path}")
        
    def set_local_config_path(self, project_dir: Path) -> None:
        """
        Set the path for the local project configuration.
        
        Args:
            project_dir: Path to the project directory
        """
        # Ensure path is absolute
        project_dir = Path(project_dir).absolute()
        self.validate_target_directory(project_dir)
        config_dir = project_dir / self.LOCAL_CONFIG_DIR
        self.local_config_path = config_dir / self.LOCAL_CONFIG_FILE
        self.global_config_path = None  # Reset global path
        logger.debug(f"Set local config path: {self.local_config_path}")
        
        # Initialize backup manager for local projects
        self._init_backup_manager(project_dir)
        
    def _init_backup_manager(self, project_dir: Path) -> None:
        """
        Initialize the backup manager for the given project directory.
        
        Args:
            project_dir: Path to the project directory
        """
        try:
            self.backup_manager = BackupManager(project_dir)
            logger.debug(f"Initialized backup manager for {project_dir}")
        except Exception as e:
            logger.warning(f"Failed to initialize backup manager: {e}")
            self.backup_manager = None
        
    def validate_target_directory(self, directory: Path) -> bool:
        """
        Validate that a directory exists and is actually a directory.
        
        Args:
            directory: Path to validate
            
        Returns:
            True if valid
            
        Raises:
            SyncError: If directory is invalid
        """
        if not directory.exists():
            raise SyncError(f"Target directory does not exist: {directory}")
        
        if not directory.is_dir():
            raise SyncError(f"Target is not a directory: {directory}")
            
        return True
        
    def create_local_mode_directory(self) -> bool:
        """
        Create the local mode directory structure if it doesn't exist.
        
        Returns:
            True if successful
            
        Raises:
            SyncError: If directory creation fails
        """
        if not self.local_config_path:
            raise SyncError("Local config path not set")
            
        config_dir = self.local_config_path.parent
        
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created local mode directory: {config_dir}")
            return True
        except Exception as e:
            error_msg = f"Failed to create local mode directory: {e}"
            logger.error(error_msg)
            raise SyncError(error_msg)
        
    def load_mode_config(self, slug: str) -> Dict[str, Any]:
        """
        Load and validate a mode configuration.
        
        Args:
            slug: Mode slug to load
            
        Returns:
            Validated mode configuration dictionary
            
        Raises:
            SyncError: If the mode file does not exist or fails validation
        """
        # Try to get the relative path from discovery cache first
        relative_path = self.discovery.get_mode_relative_path(slug)
        if relative_path:
            mode_file = self.modes_dir / relative_path
            logger.debug(f"Using cached path for {slug}: {relative_path}")
        else:
            # Fallback to simple path construction for backward compatibility
            mode_file = self.modes_dir / f"{slug}.yaml"
            logger.debug(f"Using fallback path for {slug}: {mode_file}")
        
        if not mode_file.exists():
            error_msg = f"Mode file not found: {mode_file}"
            logger.error(error_msg)
            raise SyncError(error_msg)
            
        try:
            with open(mode_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # Validate the configuration
            if self.options.get("collect_warnings", False):
                result = self.validator.validate_mode_config(
                    config, 
                    str(mode_file),
                    collect_warnings=True
                )
                
                if not result.valid:
                    error_msgs = [w["message"] for w in result.warnings if w["level"] == "error"]
                    if error_msgs:
                        error_msg = f"Validation errors in {slug}:\n" + "\n".join(error_msgs)
                        logger.error(error_msg)
                        if not self.options.get("continue_on_validation_error", False):
                            raise SyncError(error_msg)
                
                # Log warnings
                for warning in result.warnings:
                    if warning["level"] != "error":
                        logger.warning(f"{slug}: {warning['message']}")
            else:
                # Standard validation without warning collection
                self.validator.validate_mode_config(config, str(mode_file))
                
            # Strip development metadata to create clean Roo-compatible config
            config = self.validator.strip_development_metadata(config)
            
            # Ensure source is set to 'global' for sync output
            config['source'] = 'global'
            
            logger.debug(f"Successfully loaded and validated mode: {slug}")
            return config
            
        except yaml.YAMLError as e:
            error_msg = f"Error parsing YAML for {slug}: {e}"
            logger.error(error_msg)
            raise SyncError(error_msg)
        except Exception as e:
            error_msg = f"Error loading {slug}: {e}"
            logger.error(error_msg)
            raise SyncError(error_msg)
    
    def create_global_config(self, strategy_name: str = 'strategic',
                           options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create the global configuration with the specified ordering strategy.
        
        Args:
            strategy_name: Name of the ordering strategy to use
            options: Strategy-specific options
            
        Returns:
            Complete global configuration dictionary
        """
        if options is None:
            options = {}
        
        config = {'customModes': []}
        
        # Discover all modes
        categorized_modes = self.discovery.discover_all_modes()
        logger.info(f"Discovered {sum(len(modes) for modes in categorized_modes.values())} modes in {len(categorized_modes)} categories")
        
        # Create ordering strategy
        try:
            strategy_factory = OrderingStrategyFactory()
            strategy = strategy_factory.create_strategy(strategy_name)
            logger.debug(f"Using {strategy_name} ordering strategy")
        except Exception as e:
            error_msg = f"Failed to create ordering strategy: {e}"
            logger.error(error_msg)
            raise SyncError(error_msg)
        
        # Get ordered mode list
        ordered_mode_slugs = strategy.order_modes(categorized_modes, options)
        logger.debug(f"Ordered mode slugs: {ordered_mode_slugs}")
        
        # Apply exclusion filter directly here as well (in case strategy didn't)
        if 'exclude' in options and options['exclude']:
            excluded_modes = set(options['exclude'])
            ordered_mode_slugs = [mode for mode in ordered_mode_slugs if mode not in excluded_modes]
            logger.info(f"Excluded modes: {excluded_modes}")
        
        # Count of successful and failed mode loads
        success_count = 0
        failure_count = 0
        
        # Load modes in the specified order
        for mode_slug in ordered_mode_slugs:
            try:
                mode_config = self.load_mode_config(mode_slug)
                config['customModes'].append(mode_config)
                success_count += 1
            except SyncError as e:
                logger.warning(f"Skipping mode {mode_slug}: {e}")
                failure_count += 1
                # Skip modes that fail to load
                continue
        
        logger.info(f"Loaded {success_count} modes successfully, {failure_count} failed")
        return config
    
    def format_multiline_string(self, text: str, indent: int = 2) -> str:
        """
        Format a multiline string with proper YAML literal scalar syntax.
        
        Args:
            text: String to format
            indent: Indentation level
            
        Returns:
            Formatted string
        """
        if '\n' in text or len(text) > 80:
            # Use literal scalar syntax for multiline text
            prefix = ' ' * indent
            # Escape any problematic characters and ensure proper line breaks
            escaped_text = text.strip()
            # Split into lines and indent each one
            lines = escaped_text.split('\n')
            formatted_lines = [f"{prefix}{line}" for line in lines]
            return f"|-\n" + '\n'.join(formatted_lines)
        else:
            # Single line - always quote to avoid YAML parsing issues
            # Escape any double quotes in the text
            escaped_text = text.replace('"', '\\"')
            return f'"{escaped_text}"'
    
    def backup_existing_config(self) -> bool:
        """
        Create a backup of the existing config if it exists using BackupManager.
        Falls back to simple backup if BackupManager is not available.
        
        Returns:
            True if backup succeeded or wasn't needed, False if backup failed
        
        Raises:
            SyncError: If backup fails
        """
        # Determine which config path to use
        config_path = self.local_config_path if self.local_config_path else self.global_config_path
        
        if not config_path:
            error_msg = "No config path set (neither global nor local)"
            logger.error(error_msg)
            raise SyncError(error_msg)
            
        # If file doesn't exist or is empty, no backup needed
        if not config_path.exists() or config_path.stat().st_size == 0:
            return True
            
        # Try to use BackupManager for structured backups
        if self.backup_manager and self.local_config_path:
            try:
                backup_path = self.backup_manager.backup_local_roomodes()
                logger.info(f"Created BackupManager backup: {backup_path}")
                return True
            except BackupError as e:
                logger.warning(f"BackupManager backup failed, falling back to simple backup: {e}")
                # Fall through to simple backup
        
        # Fall back to simple backup for global configs or when BackupManager fails
        backup_path = config_path.with_suffix('.yaml.backup')
        try:
            shutil.copy2(config_path, backup_path)
            logger.info(f"Created simple backup: {backup_path}")
            return True
        except Exception as e:
            error_msg = f"Could not create backup: {e}"
            logger.error(error_msg)
            raise SyncError(error_msg)
    
    def check_for_complex_groups_and_warn(self) -> Dict[str, Any]:
        """
        Check if the existing global config contains complex group notation
        and generate warnings about information that will be stripped.
        
        Returns:
            Dictionary with warning information:
                - has_complex_groups: bool
                - stripped_information: dict
                - warning_messages: list
        """
        # Determine which config path to use
        config_path = self.local_config_path if self.local_config_path else self.global_config_path
        
        if not config_path or not config_path.exists():
            return {
                'has_complex_groups': False,
                'stripped_information': {},
                'warning_messages': []
            }
        
        try:
            # Load existing config
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = yaml.safe_load(f)
            
            if not existing_config or 'customModes' not in existing_config:
                return {
                    'has_complex_groups': False,
                    'stripped_information': {},
                    'warning_messages': []
                }
            
            # Check for complex groups using GlobalConfigFixer
            stripped_info = self.global_config_fixer.get_stripped_information_details(existing_config)
            warning_messages = self.global_config_fixer.generate_warning_messages(existing_config)
            
            has_complex_groups = bool(stripped_info)
            
            return {
                'has_complex_groups': has_complex_groups,
                'stripped_information': stripped_info,
                'warning_messages': warning_messages
            }
            
        except Exception as e:
            logger.warning(f"Could not check existing config for complex groups: {e}")
            return {
                'has_complex_groups': False,
                'stripped_information': {},
                'warning_messages': []
            }
    
    def write_config(self, config: Dict[str, Any]) -> bool:
        """
        Write the configuration to the config file with proper formatting.
        Uses either global or local config path based on which one is set.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if write succeeded, False otherwise
            
        Raises:
            SyncError: If write fails
        """
        # Determine which config path to use
        config_path = self.local_config_path if self.local_config_path else self.global_config_path
        
        if not config_path:
            error_msg = "No config path set (neither global nor local)"
            logger.error(error_msg)
            raise SyncError(error_msg)
            
        try:
            # Check for complex groups before writing (for backwards compatibility)
            # Note: Main warning display is handled in sync_modes, but this ensures
            # the check happens even for direct write_config calls
            warning_info = self.check_for_complex_groups_and_warn()
            if warning_info['has_complex_groups']:
                logger.warning("⚠️  Complex group notation detected in existing configuration!")
                logger.warning("The following information will be stripped during config write:")
                for warning_msg in warning_info['warning_messages']:
                    logger.warning(f"   {warning_msg}")
            
            # Apply GlobalConfigFixer to strip complex groups from the configuration
            # This is the actual fix - transform complex groups to simple groups
            fixed_config = self.global_config_fixer.fix_complex_groups(config)
            
            # Ensure the parent directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use custom YAML dumper for proper formatting and escaping with custom indentation
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(fixed_config, f, Dumper=CustomYAMLDumper, default_flow_style=False,
                         allow_unicode=True, sort_keys=False, width=float('inf'), indent=2)
            
            logger.info(f"Wrote configuration to {config_path}")
            return True
            
        except Exception as e:
            error_msg = f"Error writing configuration: {e}"
            logger.error(error_msg)
            raise SyncError(error_msg)
    
    def write_global_config(self, config: Dict[str, Any]) -> bool:
        """
        Write the configuration to the global config file.
        Alias for write_config for backward compatibility.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if write succeeded, False otherwise
        """
        if not self.global_config_path:
            error_msg = "Global config path not set"
            logger.error(error_msg)
            raise SyncError(error_msg)
            
        self.local_config_path = None  # Ensure we're writing to global
        return self.write_config(config)
        
    def sync_modes(self, strategy_name: str = 'strategic', 
                  options: Optional[Dict[str, Any]] = None,
                  dry_run: bool = False) -> bool:
        """
        Main synchronization method.
        
        Args:
            strategy_name: Name of the ordering strategy to use
            options: Strategy-specific options
            dry_run: If True, don't write config file
            
        Returns:
            True if sync succeeded, False otherwise
        """
        if options is None:
            options = {}
            
        # Merge with global options
        merged_options = self.options.copy()
        merged_options.update(options)
        options = merged_options
            
        # Check if modes directory exists
        if not self.modes_dir.exists():
            error_msg = f"Modes directory not found: {self.modes_dir}"
            logger.error(error_msg)
            raise SyncError(error_msg)
            
        # Ensure we have a config path set (either global or local)
        if not self.global_config_path and not self.local_config_path:
            error_msg = "No config path set (neither global nor local)"
            logger.error(error_msg)
            raise SyncError(error_msg)
            
        # Create local directory structure if needed
        if self.local_config_path and not dry_run:
            try:
                self.create_local_mode_directory()
            except SyncError as e:
                logger.error(f"Failed to create local directory: {e}")
                return False
        
        # Create backup if not dry run and no_backup option is not True
        if not dry_run and not options.get('no_backup', False):
            try:
                # Attempt backup before sync
                self.backup_existing_config()
                logger.info("✅ Backup created successfully before sync")
            except SyncError as e:
                logger.warning(f"⚠️ Could not create backup: {e}")
                # Continue without backup, but inform user
        elif not dry_run and options.get('no_backup', False):
            logger.info("🚫 Backup skipped due to no_backup option")
        
        # Create configuration
        try:
            logger.info(f"Creating configuration with {strategy_name} strategy")
            config = self.create_global_config(strategy_name, options)
            
            if not config['customModes']:
                logger.error("No valid modes found")
                return False
            
            # Check for complex groups and generate warnings before writing
            # (enabled by default, can be disabled with enable_complex_group_warnings=False)
            if options.get('enable_complex_group_warnings', True):
                warning_info = self.check_for_complex_groups_and_warn()
                if warning_info['has_complex_groups']:
                    logger.warning("⚠️  Complex group notation detected in existing configuration!")
                    logger.warning("The following information will be stripped during sync:")
                    for warning_msg in warning_info['warning_messages']:
                        logger.warning(f"   {warning_msg}")
                    logger.warning("This is expected behavior - sync creates simplified group notation.")
            
            # Write configuration if not dry run
            if not dry_run:
                logger.info("Writing configuration")
                return self.write_config(config)
            else:
                logger.info("Dry run - not writing configuration")
            
            return True
                
        except Exception as e:
            error_msg = f"Sync failed: {e}"
            logger.error(error_msg)
            raise SyncError(error_msg)
            
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get the current sync status with mode information.
        
        Returns:
            Dictionary with sync status information
        """
        categorized_modes = self.discovery.discover_all_modes()
        
        # Flatten the categorized modes for easier access
        all_modes = []
        mode_details = []
        
        for category, modes in categorized_modes.items():
            all_modes.extend(modes)
            
            for mode_slug in modes:
                try:
                    config = self.load_mode_config(mode_slug)
                    mode_details.append({
                        'slug': mode_slug,
                        'name': config.get('name', mode_slug),
                        'category': category,
                        'valid': True
                    })
                except SyncError:
                    mode_details.append({
                        'slug': mode_slug,
                        'name': mode_slug,
                        'category': category,
                        'valid': False
                    })
        
        # Get category information
        category_info = self.discovery.get_category_info()
        categories = []
        
        for category, info in category_info.items():
            categories.append({
                'name': category,
                'display_name': info.get('name', category),
                'icon': info.get('icon', ''),
                'count': len(categorized_modes.get(category, []))
            })
        
        return {
            'mode_count': len(all_modes),
            'categories': categories,
            'modes': mode_details
        }
    
    def sync_from_dict(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync modes based on parameters provided in a dictionary.
        This is primarily used for the MCP interface.
        
        Args:
            params: Dictionary with sync parameters:
                   - target: Path to target directory (required)
                   - strategy: Ordering strategy (optional, default: 'strategic')
                   - options: Strategy options (optional)
            
        Returns:
            Dictionary with result information:
                - success: True if sync succeeded, False otherwise
                - message: Success message if succeeded
                - error: Error message if failed
        """
        try:
            # Validate required parameters
            if 'target' not in params:
                return {
                    'success': False,
                    'error': 'Missing required parameter: target'
                }
                
            target_path = Path(params['target']).absolute()
            
            # Validate target directory
            try:
                self.validate_target_directory(target_path)
            except SyncError as e:
                return {
                    'success': False,
                    'error': f'Invalid target directory: {str(e)}'
                }
                
            # Set local config path
            self.set_local_config_path(target_path)
            
            # Get strategy and options
            strategy = params.get('strategy', 'strategic')
            options = params.get('options', {})
            
            # Set validation level if specified
            if 'validation_level' in params:
                try:
                    level_name = params['validation_level'].upper()
                    level = ValidationLevel[level_name]
                    self.validator.set_validation_level(level)
                    logger.info(f"Set validation level to {level_name} from params")
                except (KeyError, AttributeError):
                    logger.warning(f"Invalid validation level in params: {params.get('validation_level')}")
            
            # Perform sync
            success = self.sync_modes(strategy_name=strategy, options=options)
            
            if success:
                return {
                    'success': True,
                    'message': f'Successfully synced modes to {target_path}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Sync failed - no valid modes found or write error'
                }
                
        except SyncError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }