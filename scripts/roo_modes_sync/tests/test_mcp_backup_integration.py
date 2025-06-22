#!/usr/bin/env python3
"""
Test suite for MCP server backup functionality integration.

Tests to ensure MCP server provides complete backup functionality
that matches the CLI backup features.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from mcp import ModesMCPServer
    from core.backup import BackupManager, BackupError
    from exceptions import SyncError
except ImportError:
    # Fallback imports
    import sys
    script_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(script_dir / "core"))
    from mcp import ModesMCPServer
    from backup import BackupManager, BackupError
    from exceptions import SyncError


class TestMCPBackupIntegration:
    """Test MCP server backup functionality integration."""
    
    @pytest.fixture
    def modes_dir(self, tmp_path):
        """Create a temporary modes directory."""
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        return modes_dir
    
    @pytest.fixture
    def mcp_server(self, modes_dir):
        """Create MCP server instance."""
        return ModesMCPServer(modes_dir)
    
    def test_mcp_server_has_backup_tools(self, mcp_server):
        """Test that MCP server defines backup-related tools."""
        tools = mcp_server._get_tool_definitions()
        tool_names = [tool['name'] for tool in tools]
        
        # Should have all backup tools that CLI has
        expected_backup_tools = [
            'backup_modes',
            'restore_modes', 
            'list_backups'
        ]
        
        for tool_name in expected_backup_tools:
            assert tool_name in tool_names, f"Missing backup tool: {tool_name}"
    
    def test_backup_modes_tool_definition(self, mcp_server):
        """Test backup_modes tool has correct definition."""
        tools = mcp_server._get_tool_definitions()
        backup_tool = next((t for t in tools if t['name'] == 'backup_modes'), None)
        
        assert backup_tool is not None, "backup_modes tool not found"
        assert backup_tool['display_name'] == 'Backup Modes'
        assert 'description' in backup_tool
        
        schema = backup_tool['schema']
        assert schema['type'] == 'object'
        
        # Should have target parameter like sync_modes
        properties = schema['properties']
        assert 'target' in properties
        assert properties['target']['type'] == 'string'
    
    def test_restore_modes_tool_definition(self, mcp_server):
        """Test restore_modes tool has correct definition."""
        tools = mcp_server._get_tool_definitions()
        restore_tool = next((t for t in tools if t['name'] == 'restore_modes'), None)
        
        assert restore_tool is not None, "restore_modes tool not found"
        assert restore_tool['display_name'] == 'Restore Modes'
        
        schema = restore_tool['schema']
        properties = schema['properties']
        
        # Should have backup_number parameter
        assert 'backup_number' in properties
        assert properties['backup_number']['type'] == 'integer'
        
        # Should have target parameter  
        assert 'target' in properties
        assert properties['target']['type'] == 'string'
    
    def test_list_backups_tool_definition(self, mcp_server):
        """Test list_backups tool has correct definition."""
        tools = mcp_server._get_tool_definitions()
        list_tool = next((t for t in tools if t['name'] == 'list_backups'), None)
        
        assert list_tool is not None, "list_backups tool not found"
        assert list_tool['display_name'] == 'List Backups'
        
        schema = list_tool['schema']
        assert schema['type'] == 'object'
        # list_backups should have no required parameters
        assert schema['required'] == []
    
    def test_backup_modes_tool_call(self, mcp_server):
        """Test backup_modes tool call functionality."""
        request = {
            'type': 'tool_call',
            'tool': {
                'name': 'backup_modes',
                'arguments': {
                    'target': 'global'
                }
            }
        }
        
        with patch.object(mcp_server.backup_manager, 'backup_all') as mock_backup:
            mock_backup.return_value = [Path('/test/backup1'), Path('/test/backup2')]
            
            response = mcp_server.handle_request(request)
            
            assert response['type'] == 'tool_call_response'
            assert 'result' in response['content']
            mock_backup.assert_called_once()
    
    def test_restore_modes_tool_call(self, mcp_server):
        """Test restore_modes tool call functionality."""
        request = {
            'type': 'tool_call',
            'tool': {
                'name': 'restore_modes',
                'arguments': {
                    'backup_number': 1,
                    'target': 'global'
                }
            }
        }
        
        with patch.object(mcp_server.backup_manager, 'restore_global_roomodes') as mock_restore_global, \
             patch.object(mcp_server.backup_manager, 'restore_custom_modes') as mock_restore_custom:
            mock_restore_global.return_value = Path('/test/.roomodes')
            mock_restore_custom.return_value = Path('/test/custom_modes.yaml')
            
            response = mcp_server.handle_request(request)
            
            assert response['type'] == 'tool_call_response'
            assert 'result' in response['content']
            # At least one of the restore methods should be called for global target
            assert mock_restore_global.called or mock_restore_custom.called
    
    def test_list_backups_tool_call(self, mcp_server):
        """Test list_backups tool call functionality."""
        request = {
            'type': 'tool_call',
            'tool': {
                'name': 'list_backups',
                'arguments': {}
            }
        }
        
        with patch.object(mcp_server.backup_manager, 'list_available_backups') as mock_list:
            mock_list.return_value = {
                'local_roomodes': [
                    {'number': 1, 'path': Path('/test/.roomodes_1'), 'size': '1.2KB', 'file_type': 'local_roomodes', 'mtime': '2025-01-01 12:00:00'}
                ],
                'global_roomodes': [],
                'custom_modes': []
            }
            
            response = mcp_server.handle_request(request)
            
            assert response['type'] == 'tool_call_response'
            assert 'result' in response['content']
            mock_list.assert_called_once()
    
    def test_backup_error_handling(self, mcp_server):
        """Test proper error handling for backup operations."""
        request = {
            'type': 'tool_call',
            'tool': {
                'name': 'backup_modes',
                'arguments': {
                    'target': 'global'
                }
            }
        }
        
        with patch.object(mcp_server.backup_manager, 'backup_all') as mock_backup:
            mock_backup.side_effect = BackupError("Test backup error")
            
            response = mcp_server.handle_request(request)
            
            assert response['type'] == 'error'
            assert response['error']['code'] == 'BACKUP_ERROR'
            assert 'Test backup error' in response['error']['message']
    
    def test_mcp_server_initializes_backup_manager(self, modes_dir):
        """Test that MCP server properly initializes BackupManager."""
        server = ModesMCPServer(modes_dir)
        
        # Should have backup_manager attribute
        assert hasattr(server, 'backup_manager')
        assert isinstance(server.backup_manager, BackupManager)
        
        # BackupManager should be initialized with correct project root
        expected_root = modes_dir.parent  # Project root is parent of modes dir
        assert server.backup_manager.project_root == expected_root
    
    def test_hello_response_includes_backup_tools(self, mcp_server):
        """Test that hello response includes backup tools."""
        request = {'type': 'hello'}
        response = mcp_server.handle_request(request)
        
        assert response['type'] == 'hello_response'
        
        tool_names = [tool['name'] for tool in response['tools']]
        backup_tools = ['backup_modes', 'restore_modes', 'list_backups']
        
        for tool_name in backup_tools:
            assert tool_name in tool_names, f"Hello response missing backup tool: {tool_name}"
    
    def test_unknown_backup_tool_error(self, mcp_server):
        """Test error handling for unknown backup tools."""
        request = {
            'type': 'tool_call',
            'tool': {
                'name': 'unknown_backup_tool',
                'arguments': {}
            }
        }
        
        response = mcp_server.handle_request(request)
        
        assert response['type'] == 'error'
        assert response['error']['code'] == 'UNKNOWN_TOOL'
        assert 'unknown_backup_tool' in response['error']['message']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])