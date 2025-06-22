#!/usr/bin/env python3
"""
Script to apply the GlobalConfigFixer to the actual global Roo configuration file.
This fixes complex group structures that are not compatible with Roo's expected format.
"""

import sys
from pathlib import Path

# Add the roo_modes_sync module to the path
sys.path.insert(0, str(Path(__file__).parent / "roo_modes_sync"))

from roo_modes_sync.core.global_config_fixer import GlobalConfigFixer
from roo_modes_sync.utils.dynamic_paths import find_existing_custom_modes_file, get_custom_modes_path


def main():
    """Apply the global config fixer to the actual global config file."""
    
    # Find the global config file dynamically
    global_config_path = find_existing_custom_modes_file()
    
    if global_config_path is None:
        # Try VSCodium first, then VSCode
        for app_name in ["VSCodium", "Code"]:
            potential_path = get_custom_modes_path(app_name)
            if potential_path.exists():
                global_config_path = potential_path
                break
    
    if global_config_path is None:
        print("ERROR: Could not find custom_modes.yaml in any VSCode/VSCodium installation.")
        print("Searched in:")
        for app_name in ["VSCodium", "Code"]:
            print(f"  - {get_custom_modes_path(app_name)}")
        print("\nPlease ensure VSCode/VSCodium is installed and the Roo extension is active.")
        return 1
    
    # Make sure the path is absolute and normalized
    global_config_path = global_config_path.resolve()
    
    print(f"Applying GlobalConfigFixer to: {global_config_path}")
    
    if not global_config_path.exists():
        print(f"ERROR: Global config file not found at {global_config_path}")
        return 1
    
    # Initialize the fixer
    fixer = GlobalConfigFixer()
    
    # Apply the fix with comprehensive warnings and backup
    print("Analyzing current configuration...")
    result = fixer.fix_global_config_file_with_warnings(
        global_config_path,
        create_backup=True,
        preserve_as_comments=True
    )
    
    # Display results
    if result['success']:
        print(f"✅ SUCCESS: {result['message']}")
        
        if result['problematic_modes']:
            print(f"\n🔧 Fixed modes: {', '.join(result['problematic_modes'])}")
        
        if result['backup_path']:
            print(f"📁 Backup created: {result['backup_path']}")
        
        if result['warning_messages']:
            print("\n⚠️  Information stripped during fixing:")
            for warning in result['warning_messages']:
                print(f"  - {warning}")
        
        if result['stripped_information']:
            print("\n📋 Detailed stripped information:")
            for mode_slug, details in result['stripped_information'].items():
                print(f"  Mode '{mode_slug}':")
                for detail in details:
                    group_name = detail['group_name']
                    if detail.get('fileRegex'):
                        print(f"    - Group '{group_name}' fileRegex: {detail['fileRegex']}")
                    if detail.get('description'):
                        print(f"    - Group '{group_name}' description: {detail['description']}")
        
        # Validate the fixed configuration
        print("\n🔍 Validating fixed configuration...")
        validation_result = fixer.validate_fixed_config(global_config_path)
        
        if validation_result['valid']:
            print(f"✅ VALIDATION SUCCESS: {validation_result['message']}")
        else:
            print(f"❌ VALIDATION FAILED: {validation_result['message']}")
            if validation_result['issues']:
                print("Issues found:")
                for issue in validation_result['issues']:
                    print(f"  - {issue}")
            return 1
            
    else:
        print(f"❌ FAILED: {result['message']}")
        return 1
    
    print("\n🎉 Global configuration successfully fixed!")
    print("Complex group structures have been simplified to basic string format.")
    print("The Roo IDE should now properly recognize all mode configurations.")
    
    return 0


if __name__ == "__main__":
    exit(main())