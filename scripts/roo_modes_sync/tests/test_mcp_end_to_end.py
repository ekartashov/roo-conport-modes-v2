#!/usr/bin/env python3
"""
End-to-end test for MCP server functionality.

Tests the complete MCP server workflow including backup and sync operations.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

try:
    from mcp import ModesMCPServer
    from core.backup import BackupManager
    from core.sync import ModeSync
except ImportError:
    # Fallback imports
    import sys
    script_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(script_dir / "core"))
    from mcp import ModesMCPServer
    from backup import BackupManager
    from sync import ModeSync


class TestMCPEndToEnd:
    """End-to-end tests for MCP server functionality."""
    
    @pytest.fixture
    def modes_dir(self, tmp_path):
        """Create a temporary modes directory with test mode."""
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        
        # Create a test mode file
        test_mode = modes_dir / "test-mode.yaml"
        test_mode.write_text("""
slug: test-mode
name: Test Mode
groups:
  - edit
  - ask
""")
        return modes_dir
    
    @pytest.fixture
    def mcp_server(self, modes_dir):
        """Create MCP server instance."""
        return ModesMCPServer(modes_dir)
    
    def test_complete_mcp_workflow(self, mcp_server, tmp_path):
        """Test complete MCP workflow: hello -> backup -> sync -> restore."""
        
        # 1. Hello request
        hello_request = {'type': 'hello'}
        hello_response = mcp_server.handle_request(hello_request)
        
        assert hello_response['type'] == 'hello_response'
        assert hello_response['name'] == 'roo_modes_sync'
        assert len(hello_response['tools']) == 5  # sync_modes, get_sync_status, backup_modes, restore_modes, list_backups
        
        tool_names = [tool['name'] for tool in hello_response['tools']]
        expected_tools = ['sync_modes', 'get_sync_status', 'backup_modes', 'restore_modes', 'list_backups']
        for tool in expected_tools:
            assert tool in tool_names
        
        # 2. Backup request
        with patch.object(mcp_server.backup_manager, 'backup_all') as mock_backup:
            mock_backup.return_value = [Path('/test/.roomodes_1'), Path('/test/custom_modes_1.yaml')]
            
            backup_request = {
                'type': 'tool_call',
                'tool': {
                    'name': 'backup_modes',
                    'arguments': {'target': 'both'}
                }
            }
            
            backup_response = mcp_server.handle_request(backup_request)
            
            assert backup_response['type'] == 'tool_call_response'
            assert 'result' in backup_response['content']
            mock_backup.assert_called_once()
        
        # 3. Sync request
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        
        with patch.object(mcp_server.sync, 'sync_from_dict') as mock_sync:
            mock_sync.return_value = {
                'success': True,
                'message': 'Sync completed successfully',
                'modes_synced': ['test-mode']
            }
            
            sync_request = {
                'type': 'tool_call',
                'tool': {
                    'name': 'sync_modes',
                    'arguments': {
                        'target': str(target_dir),
                        'strategy': 'alphabetical'
                    }
                }
            }
            
            sync_response = mcp_server.handle_request(sync_request)
            
            assert sync_response['type'] == 'tool_call_response'
            assert sync_response['content']['result']['success'] is True
            mock_sync.assert_called_once()
        
        # 4. List backups request
        with patch.object(mcp_server.backup_manager, 'list_available_backups') as mock_list:
            mock_list.return_value = {
                'local_roomodes': [
                    {'number': 1, 'path': Path('/test/.roomodes_1'), 'size': '1.2KB', 'file_type': 'local_roomodes', 'mtime': '2025-01-01 12:00:00'}
                ],
                'global_roomodes': [],
                'custom_modes': []
            }
            
            list_request = {
                'type': 'tool_call',
                'tool': {
                    'name': 'list_backups',
                    'arguments': {}
                }
            }
            
            list_response = mcp_server.handle_request(list_request)
            
            assert list_response['type'] == 'tool_call_response'
            assert 'result' in list_response['content']
            mock_list.assert_called_once()
        
        # 5. Restore request
        with patch.object(mcp_server.backup_manager, 'restore_local_roomodes') as mock_restore:
            mock_restore.return_value = Path('/test/.roomodes')
            
            restore_request = {
                'type': 'tool_call',
                'tool': {
                    'name': 'restore_modes',
                    'arguments': {
                        'backup_number': 1,
                        'target': 'local'
                    }
                }
            }
            
            restore_response = mcp_server.handle_request(restore_request)
            
            assert restore_response['type'] == 'tool_call_response'
            assert 'result' in restore_response['content']
            mock_restore.assert_called_once()
        
        # 6. Get sync status request
        with patch.object(mcp_server.sync, 'get_sync_status') as mock_status:
            mock_status.return_value = {
                'total_modes': 1,
                'valid_modes': 1,
                'invalid_modes': 0,
                'modes': ['test-mode']
            }
            
            status_request = {
                'type': 'tool_call',
                'tool': {
                    'name': 'get_sync_status',
                    'arguments': {}
                }
            }
            
            status_response = mcp_server.handle_request(status_request)
            
            assert status_response['type'] == 'tool_call_response'
            assert status_response['content']['result']['total_modes'] == 1
            mock_status.assert_called_once()
    
    def test_mcp_error_handling_workflow(self, mcp_server):
        """Test MCP error handling across different scenarios."""
        
        # Test invalid request type
        invalid_request = {'type': 'unknown_request'}
        response = mcp_server.handle_request(invalid_request)
        
        assert response['type'] == 'error'
        assert response['error']['code'] == 'INVALID_REQUEST'
        
        # Test unknown tool
        unknown_tool_request = {
            'type': 'tool_call',
            'tool': {
                'name': 'unknown_tool',
                'arguments': {}
            }
        }
        
        response = mcp_server.handle_request(unknown_tool_request)
        
        assert response['type'] == 'error'
        assert response['error']['code'] == 'UNKNOWN_TOOL'
        
        # Test invalid restore arguments
        invalid_restore_request = {
            'type': 'tool_call',
            'tool': {
                'name': 'restore_modes',
                'arguments': {}  # Missing backup_number
            }
        }
        
        response = mcp_server.handle_request(invalid_restore_request)
        
        assert response['type'] == 'error'
        assert response['error']['code'] == 'INVALID_ARGUMENTS'
        assert 'backup_number is required' in response['error']['message']
    
    def test_mcp_resource_access(self, mcp_server):
        """Test MCP resource access functionality."""
        
        # Test valid mode resource
        with patch.object(mcp_server.sync, 'load_mode_config') as mock_load:
            mock_load.return_value = {
                'slug': 'test-mode',
                'name': 'Test Mode',
                'groups': ['edit', 'ask']
            }
            
            resource_request = {
                'type': 'resource_access',
                'uri': 'modes/test-mode'
            }
            
            response = mcp_server.handle_request(resource_request)
            
            assert response['type'] == 'resource_response'
            assert response['content']['mode']['slug'] == 'test-mode'
            mock_load.assert_called_once_with('test-mode')
        
        # Test invalid resource URI
        invalid_resource_request = {
            'type': 'resource_access',
            'uri': 'invalid/resource'
        }
        
        response = mcp_server.handle_request(invalid_resource_request)
        
        assert response['type'] == 'error'
        assert response['error']['code'] == 'INVALID_RESOURCE'
    
    def test_mcp_integration_components_initialized(self, mcp_server):
        """Test that MCP server properly initializes all required components."""
        
        # Verify ModeSync is initialized
        assert isinstance(mcp_server.sync, ModeSync)
        assert mcp_server.sync.modes_dir == mcp_server.modes_dir
        
        # Verify BackupManager is initialized
        assert isinstance(mcp_server.backup_manager, BackupManager)
        assert mcp_server.backup_manager.project_root == mcp_server.modes_dir.parent
        
        # Verify cache directories exist
        cache_dir = mcp_server.modes_dir.parent / "cache"
        if cache_dir.exists():  # Only check if cache was created
            assert (cache_dir / "roo_modes_local_backup").exists()
            assert (cache_dir / "roo_modes_global_backup").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])