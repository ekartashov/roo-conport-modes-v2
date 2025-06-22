#!/usr/bin/env python3
"""
MCP Server implementation for Roo Modes Sync.

This module provides a Model Context Protocol (MCP) server for the Roo Modes Sync functionality,
allowing direct integration with AI assistants that support MCP.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

try:
    from .core.sync import ModeSync
    from .core.backup import BackupManager, BackupError
    from .exceptions import SyncError
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir / "core"))
    sys.path.insert(0, str(script_dir))
    from core.sync import ModeSync
    from core.backup import BackupManager, BackupError
    from exceptions import SyncError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("roo_modes_mcp")


class ModesMCPServer:
    """
    MCP Server implementation for Roo Modes Sync.
    
    Provides tools for synchronizing modes via the Model Context Protocol,
    allowing AI assistants to directly manage mode configurations.
    """
    
    def __init__(self, modes_dir: Path):
        """
        Initialize the MCP server with the modes directory.
        
        Args:
            modes_dir: Path to the directory containing mode YAML files
        """
        self.modes_dir = modes_dir
        self.sync = ModeSync(modes_dir)
        # Initialize BackupManager with project root (parent of modes dir)
        project_root = modes_dir.parent
        self.backup_manager = BackupManager(project_root)
        
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP request.
        
        Args:
            request: The MCP request dictionary
            
        Returns:
            Response dictionary according to MCP protocol
        """
        try:
            request_type = request.get('type')
            
            if request_type == 'tool_call':
                return self._handle_tool_call(request)
            elif request_type == 'resource_access':
                return self._handle_resource_access(request)
            elif request_type == 'hello':
                return self._handle_hello(request)
            else:
                return {
                    'type': 'error',
                    'error': {
                        'code': 'INVALID_REQUEST',
                        'message': f'Unsupported request type: {request_type}'
                    }
                }
                
        except Exception as e:
            logger.exception("Error handling MCP request")
            return {
                'type': 'error',
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': str(e)
                }
            }
    
    def _handle_hello(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a hello request.
        
        Args:
            request: The hello request
            
        Returns:
            Hello response with server information
        """
        return {
            'type': 'hello_response',
            'name': 'roo_modes_sync',
            'display_name': 'Roo Modes Sync',
            'version': '1.0.0',
            'description': 'Synchronization tools for Roo Modes',
            'tools': self._get_tool_definitions(),
            'resources': self._get_resource_definitions()
        }
    
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get the tool definitions for the MCP server.
        
        Returns:
            List of tool definitions
        """
        return [
            {
                'name': 'sync_modes',
                'display_name': 'Sync Modes',
                'description': 'Synchronize Roo modes to a target directory',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'target': {
                            'type': 'string',
                            'description': 'Target directory path for mode configuration'
                        },
                        'strategy': {
                            'type': 'string',
                            'description': 'Ordering strategy (strategic, alphabetical, etc.)',
                            'default': 'strategic'
                        },
                        'options': {
                            'type': 'object',
                            'description': 'Strategy-specific options',
                            'default': {}
                        }
                    },
                    'required': ['target']
                }
            },
            {
                'name': 'get_sync_status',
                'display_name': 'Get Sync Status',
                'description': 'Get current sync status with mode information',
                'schema': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            },
            {
                'name': 'backup_modes',
                'display_name': 'Backup Modes',
                'description': 'Create backup of modes configuration files',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'target': {
                            'type': 'string',
                            'description': 'Target type for backup (local, global, or both)',
                            'default': 'both'
                        }
                    },
                    'required': []
                }
            },
            {
                'name': 'restore_modes',
                'display_name': 'Restore Modes',
                'description': 'Restore modes configuration from backup',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'backup_number': {
                            'type': 'integer',
                            'description': 'Backup number to restore from'
                        },
                        'target': {
                            'type': 'string',
                            'description': 'Target type for restore (local, global, or both)',
                            'default': 'both'
                        }
                    },
                    'required': ['backup_number']
                }
            },
            {
                'name': 'list_backups',
                'display_name': 'List Backups',
                'description': 'List all available backup files',
                'schema': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            }
        ]
    
    def _get_resource_definitions(self) -> List[Dict[str, Any]]:
        """
        Get the resource definitions for the MCP server.
        
        Returns:
            List of resource definitions
        """
        return [
            {
                'name': 'modes/{mode_slug}',
                'display_name': 'Mode Configuration',
                'description': 'Access to individual mode configuration',
                'parameters': {
                    'mode_slug': {
                        'type': 'string',
                        'description': 'Mode slug identifier'
                    }
                }
            }
        ]
    
    def _handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a tool call request.
        
        Args:
            request: The tool call request
            
        Returns:
            Tool call response
        """
        tool_name = request.get('tool', {}).get('name')
        arguments = request.get('tool', {}).get('arguments', {})
        
        if tool_name == 'sync_modes':
            return self._handle_sync_modes(arguments)
        elif tool_name == 'get_sync_status':
            return self._handle_get_sync_status(arguments)
        elif tool_name == 'backup_modes':
            return self._handle_backup_modes(arguments)
        elif tool_name == 'restore_modes':
            return self._handle_restore_modes(arguments)
        elif tool_name == 'list_backups':
            return self._handle_list_backups(arguments)
        else:
            return {
                'type': 'error',
                'error': {
                    'code': 'UNKNOWN_TOOL',
                    'message': f'Unknown tool: {tool_name}'
                }
            }
    
    def _handle_sync_modes(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a sync_modes tool call.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool call response
        """
        try:
            # Call the sync_from_dict method
            result = self.sync.sync_from_dict(arguments)
            
            if result.get('success', False):
                return {
                    'type': 'tool_call_response',
                    'content': {
                        'result': result
                    }
                }
            else:
                return {
                    'type': 'error',
                    'error': {
                        'code': 'SYNC_ERROR',
                        'message': result.get('error', 'Unknown sync error')
                    }
                }
                
        except Exception as e:
            logger.exception("Error in sync_modes tool call")
            return {
                'type': 'error',
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': str(e)
                }
            }
    
    def _handle_backup_modes(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a backup_modes tool call.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool call response
        """
        try:
            # Use backup_all method which returns list of backup paths
            backup_paths = self.backup_manager.backup_all()
            
            # Convert backup paths to a more informative result
            result = {
                'success': True,
                'backup_paths': [str(path) for path in backup_paths],
                'message': f'Successfully created {len(backup_paths)} backups'
            }
            
            return {
                'type': 'tool_call_response',
                'content': {
                    'result': result
                }
            }
            
        except BackupError as e:
            logger.exception("Backup error in backup_modes tool call")
            return {
                'type': 'error',
                'error': {
                    'code': 'BACKUP_ERROR',
                    'message': str(e)
                }
            }
        except Exception as e:
            logger.exception("Error in backup_modes tool call")
            return {
                'type': 'error',
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': str(e)
                }
            }
    
    def _handle_restore_modes(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a restore_modes tool call.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool call response
        """
        try:
            backup_number = arguments.get('backup_number')
            target = arguments.get('target', 'both')
            
            if backup_number is None:
                return {
                    'type': 'error',
                    'error': {
                        'code': 'INVALID_ARGUMENTS',
                        'message': 'backup_number is required'
                    }
                }
            
            # Determine which restore method to use based on target
            restored_files = []
            if target in ['local', 'both']:
                try:
                    restored_path = self.backup_manager.restore_local_roomodes()
                    restored_files.append(str(restored_path))
                except BackupError:
                    pass  # No local backups available
            
            if target in ['global', 'both']:
                try:
                    restored_path = self.backup_manager.restore_global_roomodes()
                    restored_files.append(str(restored_path))
                except BackupError:
                    pass  # No global backups available
                    
                try:
                    restored_path = self.backup_manager.restore_custom_modes()
                    restored_files.append(str(restored_path))
                except BackupError:
                    pass  # No custom modes backups available
            
            result = {
                'success': len(restored_files) > 0,
                'restored_files': restored_files,
                'message': f'Successfully restored {len(restored_files)} files' if restored_files else 'No backup files available for restore'
            }
            
            return {
                'type': 'tool_call_response',
                'content': {
                    'result': result
                }
            }
            
        except BackupError as e:
            logger.exception("Backup error in restore_modes tool call")
            return {
                'type': 'error',
                'error': {
                    'code': 'BACKUP_ERROR',
                    'message': str(e)
                }
            }
        except Exception as e:
            logger.exception("Error in restore_modes tool call")
            return {
                'type': 'error',
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': str(e)
                }
            }
    
    def _handle_list_backups(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a list_backups tool call.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool call response with backup list
        """
        try:
            result = self.backup_manager.list_available_backups()
            
            return {
                'type': 'tool_call_response',
                'content': {
                    'result': result
                }
            }
            
        except BackupError as e:
            logger.exception("Backup error in list_backups tool call")
            return {
                'type': 'error',
                'error': {
                    'code': 'BACKUP_ERROR',
                    'message': str(e)
                }
            }
        except Exception as e:
            logger.exception("Error in list_backups tool call")
            return {
                'type': 'error',
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': str(e)
                }
            }
    
    def _handle_get_sync_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a get_sync_status tool call.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tool call response with sync status
        """
        try:
            status = self.sync.get_sync_status()
            
            return {
                'type': 'tool_call_response',
                'content': {
                    'result': status
                }
            }
            
        except Exception as e:
            logger.exception("Error in get_sync_status tool call")
            return {
                'type': 'error',
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': str(e)
                }
            }
    
    def _handle_resource_access(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a resource access request.
        
        Args:
            request: The resource access request
            
        Returns:
            Resource access response
        """
        uri = request.get('uri', '')
        
        # Parse mode resource URI
        if uri.startswith('modes/'):
            mode_slug = uri[6:]  # Remove 'modes/' prefix
            return self._handle_mode_resource(mode_slug)
        else:
            return {
                'type': 'error',
                'error': {
                    'code': 'INVALID_RESOURCE',
                    'message': f'Unknown resource URI: {uri}'
                }
            }
    
    def _handle_mode_resource(self, mode_slug: str) -> Dict[str, Any]:
        """
        Handle a mode resource access.
        
        Args:
            mode_slug: Mode slug to access
            
        Returns:
            Resource access response with mode information
        """
        try:
            mode_config = self.sync.load_mode_config(mode_slug)
            
            return {
                'type': 'resource_response',
                'content': {
                    'mode': mode_config
                }
            }
            
        except SyncError as e:
            return {
                'type': 'error',
                'error': {
                    'code': 'RESOURCE_NOT_FOUND',
                    'message': str(e)
                }
            }
        except Exception as e:
            logger.exception(f"Error accessing mode resource: {mode_slug}")
            return {
                'type': 'error',
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': str(e)
                }
            }


def run_mcp_server(modes_dir: Path) -> None:
    """
    Run the MCP server.
    
    Args:
        modes_dir: Path to the modes directory
    """
    server = ModesMCPServer(modes_dir)
    
    # Process MCP stdio protocol
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = server.handle_request(request)
            json.dump(response, sys.stdout)
            sys.stdout.write('\n')
            sys.stdout.flush()
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {line}")
            error_response = {
                'type': 'error',
                'error': {
                    'code': 'INVALID_JSON',
                    'message': 'Invalid JSON in request'
                }
            }
            json.dump(error_response, sys.stdout)
            sys.stdout.write('\n')
            sys.stdout.flush()
        except Exception as e:
            logger.exception("Unexpected error in MCP server")
            error_response = {
                'type': 'error',
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': str(e)
                }
            }
            json.dump(error_response, sys.stdout)
            sys.stdout.write('\n')
            sys.stdout.flush()


if __name__ == "__main__":
    # Default to current directory if not specified
    modes_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    run_mcp_server(modes_dir)