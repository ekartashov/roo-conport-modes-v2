#!/usr/bin/env python3
"""
Command Line Interface for Roo Modes Sync.

Provides a user-friendly interface for synchronizing Roo modes:
- Global mode application (system-wide configuration)
- Local mode application (project-specific configuration)
- Mode listing and status information
- MCP server functionality
"""

import argparse
import os
import sys
import logging
from pathlib import Path
# typing imports removed as they're not used in this file

# Handle both direct execution and module imports
try:
    from .core.sync import ModeSync
    from .core.backup import BackupManager, BackupError
    from .exceptions import SyncError
    from .mcp import run_mcp_server
except ImportError:
    # Direct execution - adjust path and import
    import sys
    from pathlib import Path
    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(script_dir / "core"))
    
    from core.sync import ModeSync
    from core.backup import BackupManager, BackupError
    from exceptions import SyncError
    from mcp import run_mcp_server

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("roo_modes_cli")


def get_default_modes_dir() -> Path:
    """
    Get the default modes directory path.
    
    The path is resolved relative to the project root directory, not the current
    working directory, making the script location-independent.
    
    Returns:
        Path to the default modes directory
    """
    # Check for environment variable
    env_modes_dir = os.environ.get("ROO_MODES_DIR")
    if env_modes_dir:
        return Path(env_modes_dir)
    
    # Determine script location and project root
    # This script is at: PROJECT_ROOT/scripts/roo_modes_sync/cli.py
    # The modes directory is at: PROJECT_ROOT/modes/
    script_dir = Path(__file__).resolve().parent  # scripts/roo_modes_sync/
    project_root = script_dir.parent.parent       # PROJECT_ROOT/
    modes_dir = project_root / "modes"
    
    return modes_dir


def parse_strategy_argument(strategy_arg: str) -> tuple[str, dict]:
    """
    Parse strategy argument which can be either a strategy name or a config file path.
    
    Args:
        strategy_arg: Strategy name (e.g., "groupings") or config file path (e.g., "examples/mode-groupings/file.yaml")
        
    Returns:
        Tuple of (strategy_name, options_dict)
    """
    import yaml
    
    # Check if it's a file path (contains / or \ or ends with .yaml/.yml)
    if ('/' in strategy_arg or '\\' in strategy_arg or 
        strategy_arg.endswith('.yaml') or strategy_arg.endswith('.yml')):
        
        # It's a file path - load the configuration
        config_path = Path(strategy_arg)
        if not config_path.exists():
            raise SyncError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not isinstance(config, dict):
                raise SyncError(f"Invalid configuration file format: {config_path}")
            
            # Extract strategy name
            strategy_name = config.get('strategy')
            if not strategy_name:
                raise SyncError(f"No 'strategy' field found in configuration file: {config_path}")
            
            # Extract all other fields as options (excluding 'strategy')
            options = {k: v for k, v in config.items() if k != 'strategy'}
            
            logger.info(f"Loaded strategy '{strategy_name}' from configuration file: {config_path}")
            return strategy_name, options
            
        except yaml.YAMLError as e:
            raise SyncError(f"Error parsing configuration file {config_path}: {e}")
        except Exception as e:
            raise SyncError(f"Error loading configuration file {config_path}: {e}")
    else:
        # It's a strategy name
        return strategy_arg, {}


def sync_global(args: argparse.Namespace) -> int:
    """
    Synchronize modes to the global configuration.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Create sync object with recursive parameter
        recursive = not getattr(args, 'no_recurse', False)
        sync = ModeSync(args.modes_dir, recursive=recursive)
        
        # Set global config path if provided
        if args.config:
            sync.set_global_config_path(Path(args.config))
        else:
            sync.set_global_config_path()
            
        # Parse strategy argument - it could be a strategy name or a config file path
        strategy_name, strategy_options = parse_strategy_argument(args.strategy)
        
        # Merge strategy options with command line options
        options = {'no_backup': args.no_backup}
        options.update(strategy_options)
            
        # Perform sync
        success = sync.sync_modes(
            strategy_name=strategy_name,
            options=options,
            dry_run=args.dry_run
        )
        
        if success:
            config_path = sync.global_config_path
            action = "would be synchronized" if args.dry_run else "synchronized"
            print(f"Modes {action} to {config_path}")
            return 0
        else:
            print("Sync failed - no valid modes found or write error")
            return 1
            
    except SyncError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def sync_local(args: argparse.Namespace) -> int:
    """
    Synchronize modes to a local project directory.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Create sync object with recursive parameter
        recursive = not getattr(args, 'no_recurse', False)
        sync = ModeSync(args.modes_dir, recursive=recursive)
        
        # Set local project directory
        project_dir = Path(args.project_dir).resolve()
        sync.set_local_config_path(project_dir)
            
        # Parse strategy argument - it could be a strategy name or a config file path
        strategy_name, strategy_options = parse_strategy_argument(args.strategy)
        
        # Merge strategy options with command line options
        options = {'no_backup': args.no_backup}
        options.update(strategy_options)
            
        # Perform sync
        success = sync.sync_modes(
            strategy_name=strategy_name,
            options=options,
            dry_run=args.dry_run
        )
        
        if success:
            config_path = sync.local_config_path
            action = "would be synchronized" if args.dry_run else "synchronized"
            print(f"Modes {action} to {config_path}")
            return 0
        else:
            print("Sync failed - no valid modes found or write error")
            return 1
            
    except SyncError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def list_modes(args: argparse.Namespace) -> int:
    """
    List available modes and their status.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Create sync object with recursive parameter
        recursive = not getattr(args, 'no_recurse', False)
        sync = ModeSync(args.modes_dir, recursive=recursive)
        
        # Get sync status
        status = sync.get_sync_status()
        
        # Print status information
        print(f"Found {status['mode_count']} modes in {args.modes_dir}")
        print("\nCategories:")
        for category in status['categories']:
            print(f"  {category['icon']} {category['display_name']}: {category['count']} modes")
            
        print("\nModes:")
        for mode in status['modes']:
            valid_str = "✓" if mode['valid'] else "✗"
            print(f"  [{valid_str}] {mode['name']} ({mode['slug']}) - {mode['category']}")
            
        return 0
            
    except SyncError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


def serve_mcp(args: argparse.Namespace) -> int:
    """
    Run as an MCP server.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        print(f"Starting MCP server with modes directory: {args.modes_dir}")
        run_mcp_server(args.modes_dir)
        return 0
    except Exception as e:
        print(f"Error running MCP server: {e}")
        return 1


def backup_files(args: argparse.Namespace) -> int:
    """
    Create backups of configuration files.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Determine project directory - use workspace root if not specified
        if hasattr(args, 'project_dir') and args.project_dir:
            project_dir = Path(args.project_dir)
        else:
            # Default to workspace root (parent directory of modes directory)
            script_dir = Path(__file__).resolve().parent  # scripts/roo_modes_sync/
            project_dir = script_dir.parent.parent       # PROJECT_ROOT/
        
        backup_manager = BackupManager(project_dir)
        
        backup_files = []
        
        if args.type == 'local' or args.type == 'all':
            try:
                backup_path = backup_manager.backup_local_roomodes()
                backup_files.append(str(backup_path))
                print(f"✓ Local .roomodes backed up to: {backup_path}")
            except BackupError as e:
                print(f"⚠ Local backup failed: {e}")
                
        if args.type == 'global' or args.type == 'all':
            try:
                backup_path = backup_manager.backup_global_roomodes()
                backup_files.append(str(backup_path))
                print(f"✓ Global custom_modes.yaml backed up to: {backup_path}")
            except BackupError as e:
                print(f"⚠ Global backup failed: {e}")
        
        if backup_files:
            print(f"\n{len(backup_files)} backup(s) created successfully")
            return 0
        else:
            print("No backups were created")
            return 1
            
    except Exception as e:
        print(f"Backup operation failed: {e}")
        return 1


def restore_files(args: argparse.Namespace) -> int:
    """
    Restore configuration files from backup.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Determine project directory - use workspace root if not specified
        if hasattr(args, 'project_dir') and args.project_dir:
            project_dir = Path(args.project_dir)
        else:
            # Default to workspace root (parent directory of modes directory)
            script_dir = Path(__file__).resolve().parent  # scripts/roo_modes_sync/
            project_dir = script_dir.parent.parent       # PROJECT_ROOT/
        
        backup_manager = BackupManager(project_dir)
        
        if args.backup_file:
            # Restore specific backup file
            backup_path = Path(args.backup_file)
            if not backup_path.is_absolute():
                # Assume it's relative to cache directories
                if 'local' in backup_path.name or '.roomodes' in backup_path.name:
                    backup_path = backup_manager.local_backup_dir / backup_path.name
                else:
                    backup_path = backup_manager.global_backup_dir / backup_path.name
            
            try:
                if 'local' in backup_path.name or '.roomodes' in backup_path.name:
                    restored_path = backup_manager.restore_local_roomodes(backup_path)
                    print(f"✓ Restored local .roomodes from: {backup_path}")
                    print(f"  Restored to: {restored_path}")
                elif 'custom_modes' in backup_path.name:
                    restored_path = backup_manager.restore_custom_modes(backup_path)
                    print(f"✓ Restored custom_modes.yaml from: {backup_path}")
                    print(f"  Restored to: {restored_path}")
                elif 'global' in backup_path.name:
                    restored_path = backup_manager.restore_global_roomodes(backup_path)
                    print(f"✓ Restored global .roomodes from: {backup_path}")
                    print(f"  Restored to: {restored_path}")
                else:
                    print(f"✗ Unable to determine file type from backup name: {backup_path.name}")
                    return 1
                return 0
            except BackupError as e:
                print(f"✗ Restore failed: {e}")
                return 1
        else:
            # Restore latest backups
            restored_files = []
            
            if args.type == 'local' or args.type == 'all':
                try:
                    restored_path = backup_manager.restore_local_roomodes()
                    restored_files.append(f"Local .roomodes -> {restored_path}")
                    print(f"✓ Restored latest local .roomodes to: {restored_path}")
                except BackupError as e:
                    print(f"⚠ Local restore failed: {e}")
                    
            if args.type == 'global' or args.type == 'all':
                try:
                    restored_path = backup_manager.restore_global_roomodes()
                    restored_files.append(f"Global custom_modes.yaml -> {restored_path}")
                    print(f"✓ Restored latest global custom_modes.yaml to: {restored_path}")
                except BackupError as e:
                    print(f"⚠ Global restore failed: {e}")
            
            if restored_files:
                print(f"\n{len(restored_files)} file(s) restored successfully")
                return 0
            else:
                print("No files were restored")
                return 1
                
    except Exception as e:
        print(f"Restore operation failed: {e}")
        return 1


def list_backups(args: argparse.Namespace) -> int:
    """
    List available backup files.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Determine project directory - use workspace root if not specified
        if hasattr(args, 'project_dir') and args.project_dir:
            project_dir = Path(args.project_dir)
        else:
            # Default to workspace root (parent directory of modes directory)
            script_dir = Path(__file__).resolve().parent  # scripts/roo_modes_sync/
            project_dir = script_dir.parent.parent       # PROJECT_ROOT/
        
        backup_manager = BackupManager(project_dir)
        
        # Get all backups
        all_backups = backup_manager.list_available_backups()
        
        if not any(all_backups.values()):
            print("No backups found")
            return 0
        
        print(f"Available backups in {backup_manager.cache_dir}:\n")
        
        # Display local backups
        if all_backups['local_roomodes']:
            print("📁 Local .roomodes backups:")
            for backup_info in sorted(all_backups['local_roomodes'], key=lambda x: x['number'], reverse=True):
                print(f"  • {backup_info['path'].name} ({backup_info['size']}, {backup_info['mtime']})")
            print()
        
        # Display global custom modes backups
        if all_backups['global_custom_modes']:
            print("🌐 Global custom_modes.yaml backups:")
            for backup_info in sorted(all_backups['global_custom_modes'], key=lambda x: x['number'], reverse=True):
                print(f"  • {backup_info['path'].name} ({backup_info['size']}, {backup_info['mtime']})")
            print()
        
        total_backups = sum(len(backups) for backups in all_backups.values())
        print(f"Total: {total_backups} backup files")
        
        return 0
        
    except Exception as e:
        print(f"Error listing backups: {e}")
        return 1


def main() -> int:
    """
    Main CLI entry point.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Create main parser
    parser = argparse.ArgumentParser(
        description="Roo Modes Sync - Synchronize Roo modes configuration"
    )
    
    # Create subparsers for commands first
    subparsers = parser.add_subparsers(
        dest="command",
        help="Command to execute"
    )
    subparsers.required = True
    
    # Add global arguments as a parent parser
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument(
        "-m", "--modes-dir",
        type=Path,
        default=get_default_modes_dir(),
        help="Directory containing mode YAML files (default: modes)"
    )
    global_parser.add_argument(
        "-n", "--no-recurse",
        action="store_true",
        help="Disable recursive search for mode files in subdirectories (default: search recursively)"
    )
    
    # Sync global command
    sync_global_parser = subparsers.add_parser(
        "sync-global",
        parents=[global_parser],
        help="Synchronize modes to global configuration"
    )
    sync_global_parser.add_argument(
        "-c", "--config",
        help="Path to global configuration file (overrides default)"
    )
    sync_global_parser.add_argument(
        "-s", "--strategy",
        default="strategic",
        help="Ordering strategy (strategic, alphabetical, etc.)"
    )
    sync_global_parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="Don't write configuration file, just show what would be done"
    )
    sync_global_parser.add_argument(
        "-b", "--no-backup",
        action="store_true",
        help="Skip creating backup before sync"
    )
    sync_global_parser.set_defaults(func=sync_global)
    
    # Sync local command
    sync_local_parser = subparsers.add_parser(
        "sync-local",
        parents=[global_parser],
        help="Synchronize modes to local project directory"
    )
    sync_local_parser.add_argument(
        "project_dir",
        help="Path to project directory"
    )
    sync_local_parser.add_argument(
        "-s", "--strategy",
        default="strategic",
        help="Ordering strategy (strategic, alphabetical, etc.)"
    )
    sync_local_parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="Don't write configuration file, just show what would be done"
    )
    sync_local_parser.add_argument(
        "-b", "--no-backup",
        action="store_true",
        help="Skip creating backup before sync"
    )
    sync_local_parser.set_defaults(func=sync_local)
    
    # List command
    list_parser = subparsers.add_parser(
        "list",
        parents=[global_parser],
        help="List available modes and their status"
    )
    list_parser.set_defaults(func=list_modes)
    
    # Serve MCP command
    serve_parser = subparsers.add_parser(
        "serve",
        parents=[global_parser],
        help="Run as an MCP server"
    )
    serve_parser.set_defaults(func=serve_mcp)
    
    # Backup command
    backup_parser = subparsers.add_parser(
        "backup",
        parents=[global_parser],
        help="Create backups of configuration files",
        description="Create backups of configuration files"
    )
    backup_parser.add_argument(
        "-t", "--type",
        choices=["local", "global", "all"],
        default="all",
        help="Type of files to backup (default: all)"
    )
    backup_parser.add_argument(
        "-p", "--project-dir",
        help="Project directory (default: current directory)"
    )
    backup_parser.set_defaults(func=backup_files)
    
    # Restore command
    restore_parser = subparsers.add_parser(
        "restore",
        parents=[global_parser],
        help="Restore configuration files from backup",
        description="Restore configuration files from backup"
    )
    restore_parser.add_argument(
        "-t", "--type",
        choices=["local", "global", "all"],
        default="all",
        help="Type of files to restore (default: all - latest backups)"
    )
    restore_parser.add_argument(
        "-f", "--backup-file",
        help="Specific backup file to restore (overrides --type)"
    )
    restore_parser.add_argument(
        "-p", "--project-dir",
        help="Project directory (default: current directory)"
    )
    restore_parser.set_defaults(func=restore_files)
    
    # List backups command
    list_backups_parser = subparsers.add_parser(
        "list-backups",
        parents=[global_parser],
        help="List available backup files",
        description="List available backup files"
    )
    list_backups_parser.add_argument(
        "-p", "--project-dir",
        help="Project directory (default: current directory)"
    )
    list_backups_parser.set_defaults(func=list_backups)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run command function
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())