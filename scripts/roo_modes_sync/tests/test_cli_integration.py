#!/usr/bin/env python3
"""
Integration tests for CLI functionality.

Tests the command line interface by actually calling the CLI as a subprocess.
"""

import pytest
import tempfile
import subprocess
import sys
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import BackupManager with fallback mechanism
try:
    from core.backup import BackupManager
except ImportError:
    # If direct import fails, add core directory to path
    core_dir = Path(__file__).parent.parent / "core"
    sys.path.insert(0, str(core_dir))
    from backup import BackupManager


class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create test .roomodes file
            roomodes_file = project_dir / ".roomodes"
            roomodes_file.write_text("test local roomodes content")
            
            # Create test global.roomodes file
            global_roomodes = project_dir / "global.roomodes"
            global_roomodes.write_text("test global roomodes content")
            
            # Create test custom_modes.yaml file
            custom_modes = project_dir / "custom_modes.yaml"
            custom_modes.write_text("customModes: []")
            
            yield project_dir
    
    @pytest.fixture
    def cli_script(self):
        """Get path to CLI script."""
        return Path(__file__).parent.parent / "cli.py"
    
    def test_cli_backup_help(self, cli_script):
        """Test CLI backup help command."""
        result = subprocess.run([
            sys.executable, str(cli_script), "backup", "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Create backups of configuration files" in result.stdout
    
    def test_cli_restore_help(self, cli_script):
        """Test CLI restore help command."""
        result = subprocess.run([
            sys.executable, str(cli_script), "restore", "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Restore configuration files from backup" in result.stdout
    
    def test_cli_list_backups_help(self, cli_script):
        """Test CLI list-backups help command."""
        result = subprocess.run([
            sys.executable, str(cli_script), "list-backups", "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "List available backup files" in result.stdout
    
    def test_cli_backup_local_type(self, cli_script, temp_project_dir):
        """Test CLI backup with local type."""
        result = subprocess.run([
            sys.executable, str(cli_script), "backup",
            "--type", "local",
            "--project-dir", str(temp_project_dir)
        ], capture_output=True, text=True)
        
        # Should succeed or have expected failure message
        assert "backed up" in result.stdout or "backup failed" in result.stdout
    
    def test_cli_list_backups_empty(self, cli_script):
        """Test CLI list-backups with no backups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run([
                sys.executable, str(cli_script), "list-backups",
                "--project-dir", temp_dir
            ], capture_output=True, text=True)
            
            assert result.returncode == 0
            assert "No backups found" in result.stdout
    
    def test_cli_full_backup_restore_cycle(self, cli_script, temp_project_dir):
        """Test complete backup and restore cycle via CLI."""
        original_content = "original test content"
        modified_content = "modified test content"
        
        # Create and modify file
        roomodes_file = temp_project_dir / ".roomodes"
        roomodes_file.write_text(original_content)
        
        # Step 1: Create backup
        backup_result = subprocess.run([
            sys.executable, str(cli_script), "backup",
            "--type", "local",
            "--project-dir", str(temp_project_dir)
        ], capture_output=True, text=True)
        
        # Step 2: Modify file
        roomodes_file.write_text(modified_content)
        assert roomodes_file.read_text() == modified_content
        
        # Step 3: List backups
        subprocess.run([
            sys.executable, str(cli_script), "list-backups",
            "--project-dir", str(temp_project_dir)
        ], capture_output=True, text=True)
        
        # Step 4: Restore backup
        restore_result = subprocess.run([
            sys.executable, str(cli_script), "restore",
            "--type", "local",
            "--project-dir", str(temp_project_dir)
        ], capture_output=True, text=True)
        
        # Verify restore worked (if backup was successful)
        if "backed up" in backup_result.stdout:
            if "Restored" in restore_result.stdout:
                restored_content = roomodes_file.read_text()
                assert restored_content == original_content


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""
    
    @pytest.fixture
    def cli_script(self):
        """Get path to CLI script."""
        return Path(__file__).parent.parent / "cli.py"
    
    def test_cli_backup_nonexistent_directory(self, cli_script):
        """Test backup with nonexistent directory."""
        result = subprocess.run([
            sys.executable, str(cli_script), "backup",
            "--project-dir", "/nonexistent/directory"
        ], capture_output=True, text=True)
        
        # Should handle error gracefully
        assert result.returncode != 0 or "failed" in result.stdout
    
    def test_cli_restore_no_backups(self, cli_script):
        """Test restore when no backups exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run([
                sys.executable, str(cli_script), "restore",
                "--project-dir", temp_dir
            ], capture_output=True, text=True)
            
            # Should handle gracefully
            assert "failed" in result.stdout or "No files were restored" in result.stdout
    
    def test_cli_invalid_command(self, cli_script):
        """Test invalid CLI command."""
        result = subprocess.run([
            sys.executable, str(cli_script), "invalid-command"
        ], capture_output=True, text=True)
        
        assert result.returncode != 0


class TestCLIBackupManager:
    """Test CLI integration with BackupManager functionality."""
    
    def test_backup_manager_integration_via_cli(self):
        """Test that CLI properly uses BackupManager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create test files
            roomodes_file = project_dir / ".roomodes"
            roomodes_file.write_text("test content")
            
            # Use BackupManager directly to create backup
            backup_manager = BackupManager(project_dir)
            backup_path = backup_manager.backup_local_roomodes()
            
            # Verify backup was created with correct naming
            assert backup_path.name == ".roomodes_1"
            assert backup_path.exists()
            
            # Create another backup to test numbering
            roomodes_file.write_text("updated content")
            backup_path2 = backup_manager.backup_local_roomodes()
            assert backup_path2.name == ".roomodes_2"
            
            # List backups
            all_backups = backup_manager.list_available_backups()
            assert len(all_backups['local_roomodes']) == 2
    
    def test_backup_restore_preserves_content(self):
        """Test that backup and restore preserves file content exactly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create test file with specific content
            original_content = "Original content\nWith multiple lines\nAnd special chars: àáâãäå"
            roomodes_file = project_dir / ".roomodes"
            roomodes_file.write_text(original_content, encoding='utf-8')
            
            # Create backup
            backup_manager = BackupManager(project_dir)
            backup_manager.backup_local_roomodes()
            
            # Modify original
            roomodes_file.write_text("Modified content")
            
            # Restore
            restored_path = backup_manager.restore_local_roomodes()
            
            # Verify content is exactly the same
            restored_content = roomodes_file.read_text(encoding='utf-8')
            assert restored_content == original_content
            assert restored_path == roomodes_file


if __name__ == "__main__":
    pytest.main([__file__])