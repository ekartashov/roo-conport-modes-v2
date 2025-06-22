#!/usr/bin/env python3
"""
Tests for backup and restore functionality for Roo modes files.
"""

import pytest
import tempfile
from pathlib import Path

from roo_modes_sync.core.backup import BackupManager, BackupError


class TestBackupManager:
    """Test suite for BackupManager functionality."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create test .roomodes files
            (project_path / '.roomodes').write_text('local roomodes content')
            (project_path / 'global.roomodes').write_text('global roomodes content')
            
            # Create test custom_modes.yaml
            (project_path / 'custom_modes.yaml').write_text('custom modes content')
            
            yield project_path
    
    @pytest.fixture
    def backup_manager(self, temp_project_dir):
        """Create a BackupManager instance for testing."""
        return BackupManager(temp_project_dir)
    
    def test_backup_manager_init(self, temp_project_dir):
        """Test BackupManager initialization."""
        manager = BackupManager(temp_project_dir)
        
        assert manager.project_root == temp_project_dir
        assert manager.cache_dir == temp_project_dir / 'cache'
        assert manager.local_backup_dir == temp_project_dir / 'cache' / 'roo_modes_local_backup'
        assert manager.global_backup_dir == temp_project_dir / 'cache' / 'roo_modes_global_backup'
    
    def test_backup_manager_init_creates_directories(self, temp_project_dir):
        """Test that BackupManager creates necessary directories on init."""
        # Ensure cache directories don't exist initially
        cache_dir = temp_project_dir / 'cache'
        assert not cache_dir.exists()
        
        # Initialize BackupManager
        manager = BackupManager(temp_project_dir)
        
        # Check that directories are created
        assert manager.cache_dir.exists()
        assert manager.local_backup_dir.exists()
        assert manager.global_backup_dir.exists()
    
    def test_get_next_backup_number_empty_directory(self, backup_manager):
        """Test getting next backup number in empty directory."""
        # Ensure directories exist but are empty
        backup_manager.local_backup_dir.mkdir(parents=True, exist_ok=True)
        
        number = backup_manager._get_next_backup_number(backup_manager.local_backup_dir, '.roomodes')
        assert number == 1
    
    def test_get_next_backup_number_with_existing_backups(self, backup_manager):
        """Test getting next backup number with existing backups."""
        backup_manager.local_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create some existing backup files
        (backup_manager.local_backup_dir / '.roomodes_1').write_text('backup 1')
        (backup_manager.local_backup_dir / '.roomodes_3').write_text('backup 3')
        (backup_manager.local_backup_dir / '.roomodes_5').write_text('backup 5')
        
        number = backup_manager._get_next_backup_number(backup_manager.local_backup_dir, '.roomodes')
        assert number == 6
    
    def test_get_next_backup_number_custom_modes(self, backup_manager):
        """Test getting next backup number for custom_modes.yaml files."""
        backup_manager.global_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create existing custom_modes backups
        (backup_manager.global_backup_dir / 'custom_modes_1.yaml').write_text('backup 1')
        (backup_manager.global_backup_dir / 'custom_modes_2.yaml').write_text('backup 2')
        
        number = backup_manager._get_next_backup_number(backup_manager.global_backup_dir, 'custom_modes.yaml')
        assert number == 3
    
    def test_backup_local_roomodes_file(self, backup_manager, temp_project_dir):
        """Test backing up local .roomodes file."""
        # Create a .roomodes file
        roomodes_file = temp_project_dir / '.roomodes'
        roomodes_file.write_text('test local content')
        
        # Backup the file
        backup_path = backup_manager.backup_local_roomodes()
        
        # Check backup was created
        assert backup_path.exists()
        assert backup_path.read_text() == 'test local content'
        assert backup_path.name == '.roomodes_1'
        assert backup_path.parent == backup_manager.local_backup_dir
    
    def test_backup_global_roomodes_file(self, backup_manager, temp_project_dir):
        """Test backing up global .roomodes file."""
        # Create a global.roomodes file
        global_file = temp_project_dir / 'global.roomodes'
        global_file.write_text('test global content')
        
        # Backup the file
        backup_path = backup_manager.backup_global_roomodes()
        
        # Check backup was created
        assert backup_path.exists()
        assert backup_path.read_text() == 'test global content'
        assert backup_path.name == '.roomodes_1'
        assert backup_path.parent == backup_manager.global_backup_dir
    
    def test_backup_custom_modes_file(self, backup_manager, temp_project_dir):
        """Test backing up custom_modes.yaml file."""
        # Create a custom_modes.yaml file
        custom_file = temp_project_dir / 'custom_modes.yaml'
        custom_file.write_text('test custom modes content')
        
        # Backup the file
        backup_path = backup_manager.backup_custom_modes()
        
        # Check backup was created
        assert backup_path.exists()
        assert backup_path.read_text() == 'test custom modes content'
        assert backup_path.name == 'custom_modes_1.yaml'
        assert backup_path.parent == backup_manager.global_backup_dir
    
    def test_backup_file_not_found(self, backup_manager, temp_project_dir):
        """Test backup behavior when file doesn't exist."""
        # Remove the .roomodes file
        (temp_project_dir / '.roomodes').unlink()
        
        # Should raise BackupError
        with pytest.raises(BackupError) as exc_info:
            backup_manager.backup_local_roomodes()
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_backup_all_files(self, backup_manager, temp_project_dir):
        """Test backing up all files at once."""
        # Ensure all files exist
        (temp_project_dir / '.roomodes').write_text('local content')
        (temp_project_dir / 'global.roomodes').write_text('global content')
        (temp_project_dir / 'custom_modes.yaml').write_text('custom content')
        
        # Backup all files
        backup_paths = backup_manager.backup_all()
        
        # Check all backups were created
        assert len(backup_paths) == 3
        assert any(p.name == '.roomodes_1' for p in backup_paths)
        assert any(p.name == 'custom_modes_1.yaml' for p in backup_paths)
        
        # Check contents
        for backup_path in backup_paths:
            assert backup_path.exists()
            assert len(backup_path.read_text()) > 0
    
    def test_backup_sequential_numbering(self, backup_manager, temp_project_dir):
        """Test that sequential backups get incrementing numbers."""
        # Create and backup multiple times
        roomodes_file = temp_project_dir / '.roomodes'
        
        roomodes_file.write_text('content 1')
        backup1 = backup_manager.backup_local_roomodes()
        
        roomodes_file.write_text('content 2')
        backup2 = backup_manager.backup_local_roomodes()
        
        roomodes_file.write_text('content 3')
        backup3 = backup_manager.backup_local_roomodes()
        
        # Check sequential numbering
        assert backup1.name == '.roomodes_1'
        assert backup2.name == '.roomodes_2'
        assert backup3.name == '.roomodes_3'
        
        # Check contents
        assert backup1.read_text() == 'content 1'
        assert backup2.read_text() == 'content 2'
        assert backup3.read_text() == 'content 3'
    
    def test_get_latest_backup_number(self, backup_manager):
        """Test getting the latest backup number."""
        backup_manager.local_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # No backups exist
        latest = backup_manager._get_latest_backup_number(backup_manager.local_backup_dir, '.roomodes')
        assert latest is None
        
        # Create some backups
        (backup_manager.local_backup_dir / '.roomodes_1').write_text('backup 1')
        (backup_manager.local_backup_dir / '.roomodes_3').write_text('backup 3')
        (backup_manager.local_backup_dir / '.roomodes_2').write_text('backup 2')
        
        latest = backup_manager._get_latest_backup_number(backup_manager.local_backup_dir, '.roomodes')
        assert latest == 3
    
    def test_restore_local_roomodes_latest(self, backup_manager, temp_project_dir):
        """Test restoring the latest local .roomodes backup."""
        # Create backups
        backup_manager.local_backup_dir.mkdir(parents=True, exist_ok=True)
        (backup_manager.local_backup_dir / '.roomodes_1').write_text('backup 1')
        (backup_manager.local_backup_dir / '.roomodes_2').write_text('backup 2')
        (backup_manager.local_backup_dir / '.roomodes_3').write_text('backup 3')
        
        # Restore latest
        restored_path = backup_manager.restore_local_roomodes()
        
        # Check restoration
        assert restored_path == temp_project_dir / '.roomodes'
        assert restored_path.read_text() == 'backup 3'
        
        # Check backup file was removed
        assert not (backup_manager.local_backup_dir / '.roomodes_3').exists()
        assert (backup_manager.local_backup_dir / '.roomodes_1').exists()
        assert (backup_manager.local_backup_dir / '.roomodes_2').exists()
    
    def test_restore_specific_backup_file(self, backup_manager, temp_project_dir):
        """Test restoring a specific backup file by path."""
        # Create backups
        backup_manager.global_backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_manager.global_backup_dir / 'custom_modes_2.yaml'
        backup_file.write_text('specific backup content')
        (backup_manager.global_backup_dir / 'custom_modes_1.yaml').write_text('other backup')
        
        # Restore specific file
        restored_path = backup_manager.restore_custom_modes(backup_file_path=backup_file)
        
        # Check restoration
        assert restored_path == temp_project_dir / 'custom_modes.yaml'
        assert restored_path.read_text() == 'specific backup content'
        
        # Check specific backup file was removed
        assert not backup_file.exists()
        assert (backup_manager.global_backup_dir / 'custom_modes_1.yaml').exists()
    
    def test_restore_no_backups_available(self, backup_manager):
        """Test restore behavior when no backups are available."""
        # Ensure backup directories are empty
        backup_manager.local_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Should raise BackupError
        with pytest.raises(BackupError) as exc_info:
            backup_manager.restore_local_roomodes()
        
        assert "no" in str(exc_info.value).lower() and "backups available" in str(exc_info.value).lower()
    
    def test_restore_specific_file_not_found(self, backup_manager):
        """Test restore behavior when specific backup file doesn't exist."""
        nonexistent_file = backup_manager.local_backup_dir / '.roomodes_999'
        
        with pytest.raises(BackupError) as exc_info:
            backup_manager.restore_local_roomodes(backup_file_path=nonexistent_file)
        
        assert "backup file not found" in str(exc_info.value).lower()
    
    def test_list_available_backups(self, backup_manager):
        """Test listing available backup files."""
        # Create various backup files
        backup_manager.local_backup_dir.mkdir(parents=True, exist_ok=True)
        backup_manager.global_backup_dir.mkdir(parents=True, exist_ok=True)
        
        (backup_manager.local_backup_dir / '.roomodes_1').write_text('local 1')
        (backup_manager.local_backup_dir / '.roomodes_3').write_text('local 3')
        (backup_manager.global_backup_dir / '.roomodes_2').write_text('global 2')
        (backup_manager.global_backup_dir / 'custom_modes_1.yaml').write_text('custom 1')
        (backup_manager.global_backup_dir / 'custom_modes_4.yaml').write_text('custom 4')
        
        # List backups
        backups = backup_manager.list_available_backups()
        
        # Check structure
        assert 'local_roomodes' in backups
        assert 'global_roomodes' in backups
        assert 'custom_modes' in backups
        
        # Check local backups
        local_backups = backups['local_roomodes']
        assert len(local_backups) == 2
        assert any(b['number'] == 1 for b in local_backups)
        assert any(b['number'] == 3 for b in local_backups)
        
        # Check global backups
        global_backups = backups['global_roomodes']
        assert len(global_backups) == 1
        assert global_backups[0]['number'] == 2
        
        # Check custom mode backups
        custom_backups = backups['custom_modes']
        assert len(custom_backups) == 2
        assert any(b['number'] == 1 for b in custom_backups)
        assert any(b['number'] == 4 for b in custom_backups)
    
    def test_backup_error_exception(self):
        """Test BackupError exception functionality."""
        error = BackupError("test error message")
        assert str(error) == "test error message"
        assert isinstance(error, Exception)
    
    def test_backup_manager_with_nonexistent_project_root(self):
        """Test BackupManager with nonexistent project root."""
        nonexistent_path = Path("/nonexistent/path")
        
        with pytest.raises(BackupError) as exc_info:
            BackupManager(nonexistent_path)
        
        assert "project root does not exist" in str(exc_info.value).lower()
    
    def test_backup_preserves_file_permissions(self, backup_manager, temp_project_dir):
        """Test that backup preserves original file permissions."""
        
        # Create a file with specific permissions
        roomodes_file = temp_project_dir / '.roomodes'
        roomodes_file.write_text('test content')
        roomodes_file.chmod(0o644)
        
        # Backup the file
        backup_path = backup_manager.backup_local_roomodes()
        
        # Check permissions are preserved
        original_permissions = roomodes_file.stat().st_mode & 0o777
        backup_permissions = backup_path.stat().st_mode & 0o777
        assert original_permissions == backup_permissions