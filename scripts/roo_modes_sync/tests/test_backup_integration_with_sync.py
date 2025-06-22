#!/usr/bin/env python3
"""
Test backup integration with sync commands and no-backup option.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from ..core.sync import ModeSync
    from ..core.backup import BackupManager, BackupError
    from ..exceptions import SyncError
except ImportError:
    import sys
    from pathlib import Path
    script_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(script_dir / "core"))
    
    from core.sync import ModeSync
    from core.backup import BackupManager, BackupError
    from exceptions import SyncError


class TestBackupIntegrationWithSync:
    """Test backup functionality is properly integrated with sync commands."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directories
        self.temp_dir = Path(tempfile.mkdtemp())
        self.modes_dir = self.temp_dir / "modes"
        self.project_dir = self.temp_dir / "project"
        self.global_config_dir = self.temp_dir / "global"
        
        # Create directories
        self.modes_dir.mkdir(parents=True)
        self.project_dir.mkdir(parents=True)
        self.global_config_dir.mkdir(parents=True)
        
        # Create a test mode file
        test_mode = self.modes_dir / "test-mode.yaml"
        test_mode.write_text("""
slug: test-mode
name: Test Mode
roleDefinition: Test role definition
customInstructions: Test instructions
groups:
  - read
source: global
""")
        
        # Create existing config files to test backup
        self.existing_global_config = self.global_config_dir / "custom_modes.yaml"
        self.existing_global_config.write_text("customModes:\n  - slug: old-mode\n    name: Old Mode")
        
        self.existing_local_config = self.project_dir / ".roomodes" / "modes.yaml"
        self.existing_local_config.parent.mkdir(exist_ok=True)
        self.existing_local_config.write_text("customModes:\n  - slug: old-local-mode\n    name: Old Local Mode")

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_sync_global_creates_backup_by_default(self):
        """Test that sync-global creates backup by default when config exists."""
        sync = ModeSync(self.modes_dir)
        sync.set_global_config_path(self.existing_global_config)
        
        # Mock backup manager to verify backup is called
        with patch.object(sync, 'backup_existing_config') as mock_backup:
            mock_backup.return_value = True
            
            result = sync.sync_modes(strategy_name='alphabetical', options={})
            
            # Verify backup was called
            mock_backup.assert_called_once()
            assert result is True

    def test_sync_local_creates_backup_by_default(self):
        """Test that sync-local creates backup by default when config exists."""
        sync = ModeSync(self.modes_dir)
        sync.set_local_config_path(self.project_dir)
        
        # Mock backup manager to verify backup is called
        with patch.object(sync, 'backup_existing_config') as mock_backup:
            mock_backup.return_value = True
            
            result = sync.sync_modes(strategy_name='alphabetical', options={})
            
            # Verify backup was called
            mock_backup.assert_called_once()
            assert result is True

    def test_sync_global_skips_backup_with_no_backup_option(self):
        """Test that sync-global skips backup when no_backup option is True."""
        sync = ModeSync(self.modes_dir)
        sync.set_global_config_path(self.existing_global_config)
        
        # Mock backup manager to verify backup is NOT called
        with patch.object(sync, 'backup_existing_config') as mock_backup:
            
            result = sync.sync_modes(
                strategy_name='alphabetical', 
                options={'no_backup': True}
            )
            
            # Verify backup was NOT called
            mock_backup.assert_not_called()
            assert result is True

    def test_sync_local_skips_backup_with_no_backup_option(self):
        """Test that sync-local skips backup when no_backup option is True."""
        sync = ModeSync(self.modes_dir)
        sync.set_local_config_path(self.project_dir)
        
        # Mock backup manager to verify backup is NOT called
        with patch.object(sync, 'backup_existing_config') as mock_backup:
            
            result = sync.sync_modes(
                strategy_name='alphabetical', 
                options={'no_backup': True}
            )
            
            # Verify backup was NOT called
            mock_backup.assert_not_called()
            assert result is True

    def test_sync_continues_on_backup_failure(self):
        """Test that sync continues when backup fails but logs warning."""
        sync = ModeSync(self.modes_dir)
        sync.set_global_config_path(self.existing_global_config)
        
        # Mock backup to fail
        with patch.object(sync, 'backup_existing_config') as mock_backup:
            mock_backup.side_effect = SyncError("Backup failed")
            
            # Should continue and return True despite backup failure
            with patch('logging.Logger.warning') as mock_warning:
                result = sync.sync_modes(strategy_name='alphabetical', options={})
                
                # Verify backup was attempted
                mock_backup.assert_called_once()
                # Verify warning was logged
                mock_warning.assert_called()
                # Verify sync still succeeded
                assert result is True

    def test_sync_from_dict_respects_no_backup_option(self):
        """Test that sync_from_dict respects no_backup option."""
        sync = ModeSync(self.modes_dir)
        
        # Mock backup manager to verify backup behavior
        with patch.object(sync, 'backup_existing_config') as mock_backup:
            
            # Test with no_backup=True
            result = sync.sync_from_dict({
                'target': str(self.project_dir),
                'strategy': 'alphabetical',
                'options': {'no_backup': True}
            })
            
            # Verify backup was NOT called
            mock_backup.assert_not_called()
            assert result['success'] is True

    def test_sync_from_dict_creates_backup_by_default(self):
        """Test that sync_from_dict creates backup by default."""
        sync = ModeSync(self.modes_dir)
        
        # Mock backup manager to verify backup behavior
        with patch.object(sync, 'backup_existing_config') as mock_backup:
            mock_backup.return_value = True
            
            # Test without no_backup option (should backup by default)
            result = sync.sync_from_dict({
                'target': str(self.project_dir),
                'strategy': 'alphabetical'
            })
            
            # Verify backup was called
            mock_backup.assert_called_once()
            assert result['success'] is True

    def test_dry_run_skips_backup(self):
        """Test that dry run skips backup operation."""
        sync = ModeSync(self.modes_dir)
        sync.set_global_config_path(self.existing_global_config)
        
        # Mock backup manager to verify backup is NOT called during dry run
        with patch.object(sync, 'backup_existing_config') as mock_backup:
            
            result = sync.sync_modes(
                strategy_name='alphabetical', 
                options={},
                dry_run=True
            )
            
            # Verify backup was NOT called during dry run
            mock_backup.assert_not_called()
            assert result is True

    def test_backup_success_message_logged(self):
        """Test that successful backup logs appropriate message."""
        sync = ModeSync(self.modes_dir)
        sync.set_global_config_path(self.existing_global_config)
        
        with patch.object(sync, 'backup_existing_config') as mock_backup:
            mock_backup.return_value = True
            with patch('logging.Logger.info') as mock_info:
                
                sync.sync_modes(strategy_name='alphabetical', options={})
                
                # Check that success message was logged
                mock_info.assert_any_call("✅ Backup created successfully before sync")

    def test_no_backup_option_in_sync_options(self):
        """Test that no_backup option is properly handled in sync options."""
        sync = ModeSync(self.modes_dir)
        sync.set_global_config_path(self.existing_global_config)
        
        # Set global options with no_backup
        sync.set_options({'no_backup': True})
        
        with patch.object(sync, 'backup_existing_config') as mock_backup:
            
            result = sync.sync_modes(strategy_name='alphabetical', options={})
            
            # Verify backup was NOT called due to global option
            mock_backup.assert_not_called()
            assert result is True