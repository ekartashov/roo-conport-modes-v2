#!/usr/bin/env python3
"""
CLI script to fix complex group structures in global Roo configuration.

This script identifies and fixes problematic group structures in the global
Roo configuration file that contain fileRegex and description fields, which
are not supported by Roo and cause format errors.
"""

import argparse
import sys
from pathlib import Path

from core.global_config_fixer import GlobalConfigFixer


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Fix complex group structures in global Roo configuration files'
    )
    
    parser.add_argument(
        'config_path',
        help='Path to the global Roo configuration file (custom_modes.yaml)'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating a backup before making changes'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate the configuration without making changes'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Convert path to Path object
    config_path = Path(args.config_path)
    
    # Initialize the fixer
    fixer = GlobalConfigFixer()
    
    if args.validate_only:
        # Validation only mode
        print(f"Validating configuration: {config_path}")
        
        if not config_path.exists():
            print(f"ERROR: Configuration file not found: {config_path}")
            sys.exit(1)
        
        result = fixer.validate_fixed_config(config_path)
        
        print(f"Validation result: {result['message']}")
        
        if result['issues']:
            print("\nIssues found:")
            for issue in result['issues']:
                print(f"  - {issue}")
        
        sys.exit(0 if result['valid'] else 1)
    
    else:
        # Fix mode
        print(f"Fixing global Roo configuration: {config_path}")
        
        if not config_path.exists():
            print(f"ERROR: Configuration file not found: {config_path}")
            sys.exit(1)
        
        # Load and analyze current state
        try:
            config_data = fixer.load_global_config(config_path)
            problematic_modes = fixer.identify_problematic_modes(config_data)
            
            if args.verbose:
                print(f"Found {len(config_data)} modes in configuration")
                if problematic_modes:
                    print(f"Problematic modes with complex groups: {', '.join(problematic_modes)}")
                else:
                    print("No problematic modes found")
            
        except Exception as e:
            print(f"ERROR: Failed to analyze configuration: {e}")
            sys.exit(1)
        
        # Apply the fix
        result = fixer.fix_global_config_file(
            config_path, 
            create_backup=not args.no_backup
        )
        
        if result['success']:
            print(f"SUCCESS: {result['message']}")
            
            if result['backup_path']:
                print(f"Backup created: {result['backup_path']}")
            
            if args.verbose and result['problematic_modes']:
                print(f"Fixed modes: {', '.join(result['problematic_modes'])}")
            
            # Validate the fix
            validation_result = fixer.validate_fixed_config(config_path)
            if validation_result['valid']:
                print("Validation: Configuration is now valid")
            else:
                print("WARNING: Validation found remaining issues:")
                for issue in validation_result['issues']:
                    print(f"  - {issue}")
            
        else:
            print(f"ERROR: {result['message']}")
            sys.exit(1)


if __name__ == '__main__':
    main()