#!/usr/bin/env python3
"""
Integration tests for backup functionality with the sync system.
"""

import pytest
import tempfile
from pathlib import Path

from roo_modes_sync.core.backup import BackupManager, BackupError
from roo_modes_sync.core.sync import ModeSync


class TestBackupIntegration:
    """Test backup integration with sync operations."""
    
    @pytest.fixture
    def temp_project_setup(self):
        """Create a temporary project setup with modes and sync configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a modes directory with test modes
            modes_dir = project_path / 'modes'
            modes_dir.mkdir()
            
            # Create test mode files
            (modes_dir / 'test-mode.yaml').write_text("""
slug: test-mode
name: Test Mode
roleDefinition: Test role definition
groups:
  - read
  - edit:
      fileRegex: \\.txt$
      description: Text files only
""".strip())
            
            # Create existing .roomodes and custom_modes.yaml files
            (project_path / '.roomodes').write_text('existing local roomodes')
            (project_path / 'global.roomodes').write_text('existing global roomodes')
            (project_path / 'custom_modes.yaml').write_text('existing custom modes')
            
            yield project_path
    
    @pytest.fixture
    def sync_with_backup(self, temp_project_setup):
        """Create ModeSync instance with backup integration."""
        sync = ModeSync(str(temp_project_setup / 'modes'))
        sync.backup_manager = BackupManager(temp_project_setup)
        return sync, temp_project_setup
    
    def test_sync_creates_backup_before_overwrite(self, sync_with_backup):
        """Test that sync operations create backups before overwriting files."""
        sync, project_path = sync_with_backup
        
        # Set target paths
        # Target files exist and should be backed up before sync
        # local_target = project_path / '.roomodes'
        # global_target = project_path / 'global.roomodes'
        
        # Ensure backup manager creates directories
        backup_manager = sync.backup_manager
        
        # Create backups before sync
        local_backup = backup_manager.backup_local_roomodes()
        global_backup = backup_manager.backup_global_roomodes()
        
        # Verify backups were created
        assert local_backup.exists()
        assert global_backup.exists()
        assert local_backup.read_text() == 'existing local roomodes'
        assert global_backup.read_text() == 'existing global roomodes'
        
        # Verify backup file names follow numbering convention
        assert local_backup.name == '.roomodes_1'
        assert global_backup.name == '.roomodes_1'
    
    def test_multiple_sync_operations_increment_backup_numbers(self, sync_with_backup):
        """Test that multiple sync operations create incrementally numbered backups."""
        sync, project_path = sync_with_backup
        backup_manager = sync.backup_manager
        
        # Modify and backup multiple times
        roomodes_file = project_path / '.roomodes'
        
        # First backup
        roomodes_file.write_text('version 1')
        backup1 = backup_manager.backup_local_roomodes()
        
        # Second backup
        roomodes_file.write_text('version 2')
        backup2 = backup_manager.backup_local_roomodes()
        
        # Third backup
        roomodes_file.write_text('version 3')
        backup3 = backup_manager.backup_local_roomodes()
        
        # Verify sequential numbering
        assert backup1.name == '.roomodes_1'
        assert backup2.name == '.roomodes_2'
        assert backup3.name == '.roomodes_3'
        
        # Verify contents
        assert backup1.read_text() == 'version 1'
        assert backup2.read_text() == 'version 2'
        assert backup3.read_text() == 'version 3'
    
    def test_restore_functionality_with_sync(self, sync_with_backup):
        """Test restore functionality after sync operations."""
        sync, project_path = sync_with_backup
        backup_manager = sync.backup_manager
        
        # Create original content and backup
        original_content = 'original roomodes content'
        roomodes_file = project_path / '.roomodes'
        roomodes_file.write_text(original_content)
        backup_manager.backup_local_roomodes()
        
        # Simulate sync operation changing the file
        roomodes_file.write_text('modified by sync operation')
        assert roomodes_file.read_text() == 'modified by sync operation'
        
        # Restore from backup
        restored_path = backup_manager.restore_local_roomodes()
        
        # Verify restoration
        assert restored_path == roomodes_file
        assert roomodes_file.read_text() == original_content
        
        # Verify backup file was removed after restore
        backup_files = list(backup_manager.local_backup_dir.glob('.roomodes_*'))
        assert len(backup_files) == 0
    
    def test_list_backups_after_sync_operations(self, sync_with_backup):
        """Test listing backups after various sync operations."""
        sync, project_path = sync_with_backup
        backup_manager = sync.backup_manager
        
        # Create multiple backups of different types
        (project_path / '.roomodes').write_text('local 1')
        backup_manager.backup_local_roomodes()
        
        (project_path / 'global.roomodes').write_text('global 1')
        backup_manager.backup_global_roomodes()
        
        (project_path / 'custom_modes.yaml').write_text('custom 1')
        backup_manager.backup_custom_modes()
        
        (project_path / '.roomodes').write_text('local 2')
        backup_manager.backup_local_roomodes()
        
        # List all backups
        backups = backup_manager.list_available_backups()
        
        # Verify backup structure
        assert len(backups['local_roomodes']) == 2
        assert len(backups['global_roomodes']) == 1
        assert len(backups['custom_modes']) == 1
        
        # Verify backup details
        local_backups = sorted(backups['local_roomodes'], key=lambda x: x['number'])
        assert local_backups[0]['number'] == 1
        assert local_backups[1]['number'] == 2
        
        global_backups = backups['global_roomodes']
        assert global_backups[0]['number'] == 1
        
        custom_backups = backups['custom_modes']
        assert custom_backups[0]['number'] == 1
    
    def test_backup_all_files_integration(self, sync_with_backup):
        """Test backing up all files at once in integration scenario."""
        sync, project_path = sync_with_backup
        backup_manager = sync.backup_manager
        
        # Ensure all target files exist with specific content
        (project_path / '.roomodes').write_text('local content for backup')
        (project_path / 'global.roomodes').write_text('global content for backup')
        (project_path / 'custom_modes.yaml').write_text('custom content for backup')
        
        # Backup all files
        backup_paths = backup_manager.backup_all()
        
        # Verify all backups were created
        assert len(backup_paths) == 3
        
        # Verify file types
        backup_names = [p.name for p in backup_paths]
        assert '.roomodes_1' in backup_names
        assert 'custom_modes_1.yaml' in backup_names
        
        # Verify content preservation
        for backup_path in backup_paths:
            assert backup_path.exists()
            content = backup_path.read_text()
            assert 'content for backup' in content
    
    def test_graceful_failure_when_no_files_to_backup(self, sync_with_backup):
        """Test graceful behavior when backup files don't exist."""
        sync, project_path = sync_with_backup
        backup_manager = sync.backup_manager
        
        # Remove all potential backup targets
        (project_path / '.roomodes').unlink()
        (project_path / 'global.roomodes').unlink()
        (project_path / 'custom_modes.yaml').unlink()
        
        # Attempt to backup individual files should raise errors
        with pytest.raises(BackupError):
            backup_manager.backup_local_roomodes()
        
        with pytest.raises(BackupError):
            backup_manager.backup_global_roomodes()
        
        with pytest.raises(BackupError):
            backup_manager.backup_custom_modes()
        
        # backup_all should return empty list when no files exist
        backup_paths = backup_manager.backup_all()
        assert backup_paths == []
    
    def test_restore_specific_backup_by_path(self, sync_with_backup):
        """Test restoring a specific backup file by providing its path."""
        sync, project_path = sync_with_backup
        backup_manager = sync.backup_manager
        
        # Create multiple backups
        roomodes_file = project_path / '.roomodes'
        
        roomodes_file.write_text('backup content 1')
        backup1 = backup_manager.backup_local_roomodes()
        
        roomodes_file.write_text('backup content 2')
        backup2 = backup_manager.backup_local_roomodes()
        
        roomodes_file.write_text('backup content 3')
        backup3 = backup_manager.backup_local_roomodes()
        
        # Modify file to something different
        roomodes_file.write_text('current modified content')
        
        # Restore specific backup (backup2)
        restored_path = backup_manager.restore_local_roomodes(backup_file_path=backup2)
        
        # Verify restoration
        assert restored_path == roomodes_file
        assert roomodes_file.read_text() == 'backup content 2'
        
        # Verify only backup2 was removed
        assert not backup2.exists()
        assert backup1.exists()
        assert backup3.exists()
    
    def test_cache_directory_structure_creation(self, temp_project_setup):
        """Test that cache directory structure is created properly."""
        # Initially no cache directory
        cache_dir = temp_project_setup / 'cache'
        assert not cache_dir.exists()
        
        # Initialize backup manager
        backup_manager = BackupManager(temp_project_setup)
        
        # Verify directory structure was created
        assert cache_dir.exists()
        assert backup_manager.local_backup_dir.exists()
        assert backup_manager.global_backup_dir.exists()
        
        # Verify exact paths
        assert backup_manager.local_backup_dir == cache_dir / 'roo_modes_local_backup'
        assert backup_manager.global_backup_dir == cache_dir / 'roo_modes_global_backup'
    
    def test_backup_error_handling_in_integration(self, sync_with_backup):
        """Test error handling in integration scenarios."""
        sync, project_path = sync_with_backup
        backup_manager = sync.backup_manager
        
        # Test restore with nonexistent backup file
        nonexistent_backup = backup_manager.local_backup_dir / '.roomodes_999'
        
        with pytest.raises(BackupError) as exc_info:
            backup_manager.restore_local_roomodes(backup_file_path=nonexistent_backup)
        
        assert "backup file not found" in str(exc_info.value).lower()
        
        # Test restore with no backups available
        with pytest.raises(BackupError) as exc_info:
            backup_manager.restore_custom_modes()
        
        assert "backups available" in str(exc_info.value).lower()