"""Test cases for mode discovery functionality."""

import os
import yaml
import pytest
from pathlib import Path
from typing import Dict, List, Any, Optional

from roo_modes_sync.core.discovery import ModeDiscovery


class TestModeDiscovery:
    """Test cases for ModeDiscovery class."""
    
    @pytest.fixture
    def temp_modes_dir(self, tmp_path):
        """Create a temporary directory for test mode files."""
        modes_dir = tmp_path / "modes"
        modes_dir.mkdir()
        return modes_dir
    
    def create_mode_file(self, modes_dir: Path, slug: str, config: Dict[str, Any]) -> Path:
        """Helper to create a mode file in the test directory."""
        mode_file = modes_dir / f"{slug}.yaml"
        with open(mode_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return mode_file
        
    def create_valid_mode_config(self, slug: str, expected_category: str = None) -> Dict[str, Any]:
        """Helper to create a valid mode configuration."""
        config = {
            'slug': slug,
            'name': f'{slug.title()} Mode',
            'roleDefinition': f'Test {slug} role definition',
            'groups': ['read', 'edit']
        }
        
        if expected_category:
            config['expected_category'] = expected_category
            
        return config
    
    def test_init(self, temp_modes_dir):
        """Test ModeDiscovery initialization."""
        discovery = ModeDiscovery(temp_modes_dir)
        assert discovery.modes_dir == temp_modes_dir
        assert hasattr(discovery, 'category_patterns')
    
    def test_discover_all_modes(self, temp_modes_dir):
        """Test that modes are properly discovered and categorized."""
        # Create test mode files
        self.create_mode_file(temp_modes_dir, "code", self.create_valid_mode_config("code", "core"))
        self.create_mode_file(temp_modes_dir, "architect", self.create_valid_mode_config("architect", "core"))
        self.create_mode_file(temp_modes_dir, "code-enhanced", self.create_valid_mode_config("code-enhanced", "enhanced"))
        self.create_mode_file(temp_modes_dir, "security-auditor", self.create_valid_mode_config("security-auditor", "specialized"))
        self.create_mode_file(temp_modes_dir, "custom", self.create_valid_mode_config("custom", "discovered"))
        
        # Create an invalid mode file
        invalid_file = temp_modes_dir / "invalid.yaml"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content")
        
        # Initialize discovery with temp directory
        discovery = ModeDiscovery(temp_modes_dir)
        
        # Test discovery results
        modes = discovery.discover_all_modes()
        
        # Verify correct categorization
        assert "code" in modes["core"]
        assert "architect" in modes["core"]
        assert "code-enhanced" in modes["enhanced"]
        assert "security-auditor" in modes["specialized"]
        assert "custom" in modes["discovered"]
        
        # Verify invalid file is not included
        assert "invalid" not in modes["core"]
        assert "invalid" not in modes["enhanced"]
        assert "invalid" not in modes["specialized"]
        assert "invalid" not in modes["discovered"]
        
        # Verify mode count
        assert discovery.get_mode_count() == 5
    
    def test_categorize_mode(self):
        """Test that mode slugs are correctly categorized."""
        discovery = ModeDiscovery(Path("/tmp"))
        
        # Test core category
        assert discovery.categorize_mode("code") == "core"
        assert discovery.categorize_mode("architect") == "core"
        assert discovery.categorize_mode("debug") == "core"
        assert discovery.categorize_mode("ask") == "core"
        
        # Test enhanced category
        assert discovery.categorize_mode("code-enhanced") == "enhanced"
        assert discovery.categorize_mode("debug-plus") == "enhanced"
        
        # Test specialized category
        assert discovery.categorize_mode("code-maintenance") == "specialized"
        assert discovery.categorize_mode("prompt-enhancer") == "specialized"
        assert discovery.categorize_mode("diagram-creator") == "specialized"
        assert discovery.categorize_mode("security-auditor") == "specialized"
        
        # Test discovered category (fallback)
        assert discovery.categorize_mode("custom") == "discovered"
        assert discovery.categorize_mode("test") == "discovered"
    
    def test_nonexistent_directory(self, tmp_path):
        """Test that discovery handles non-existent directories gracefully."""
        # Create a path to a directory that doesn't exist
        nonexistent_path = tmp_path / "nonexistent_directory"
        
        # Ensure the path doesn't exist
        assert not nonexistent_path.exists()
        
        # Initialize discovery with non-existent path
        discovery = ModeDiscovery(nonexistent_path)
        
        # Discovery should return empty categories
        modes = discovery.discover_all_modes()
        assert modes["core"] == []
        assert modes["enhanced"] == []
        assert modes["specialized"] == []
        assert modes["discovered"] == []
        
        # Mode count should be 0
        assert discovery.get_mode_count() == 0
    
    def test_is_valid_mode_file(self, temp_modes_dir):
        """Test validation of mode files."""
        # Create a valid mode file
        valid_file = temp_modes_dir / "valid.yaml"
        with open(valid_file, 'w', encoding='utf-8') as f:
            yaml.dump({
                'slug': 'valid',
                'name': 'Valid Mode',
                'roleDefinition': 'This is a valid mode',
                'groups': ['test']
            }, f)
        
        # Create an invalid mode file (missing required fields)
        invalid_file = temp_modes_dir / "invalid.yaml"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            yaml.dump({
                'slug': 'invalid',
                'name': 'Invalid Mode'
                # Missing roleDefinition and groups
            }, f)
        
        # Create a corrupt YAML file
        corrupt_file = temp_modes_dir / "corrupt.yaml"
        with open(corrupt_file, 'w', encoding='utf-8') as f:
            f.write("corrupt: yaml: content:\n  - missing: colon\n  indentation error")
        
        # Initialize discovery
        discovery = ModeDiscovery(temp_modes_dir)
        
        # Test _is_valid_mode_file (using name mangling to access private method)
        assert discovery._is_valid_mode_file(valid_file) is True
        assert discovery._is_valid_mode_file(invalid_file) is False
        assert discovery._is_valid_mode_file(corrupt_file) is False
        
        # Test with non-existent file
        assert discovery._is_valid_mode_file(temp_modes_dir / "nonexistent.yaml") is False
    
    def test_get_category_info(self):
        """Test that category information is provided correctly."""
        discovery = ModeDiscovery(Path("/tmp"))
        
        # Get category info
        categories = discovery.get_category_info()
        
        # Verify categories are present
        assert "core" in categories
        assert "enhanced" in categories
        assert "specialized" in categories
        assert "discovered" in categories
        
        # Verify category information fields
        for category in categories.values():
            assert "icon" in category
            assert "name" in category
            assert "description" in category
    
    def test_find_mode_by_name(self, temp_modes_dir):
        """Test finding a mode by its display name."""
        # Create test modes
        modes = {
            "test-mode": "Test Mode",
            "another-mode": "Another Test Mode",
            "special-mode": "Special Testing Mode"
        }
        
        for slug, name in modes.items():
            config = self.create_valid_mode_config(slug)
            config["name"] = name
            self.create_mode_file(temp_modes_dir, slug, config)
        
        discovery = ModeDiscovery(temp_modes_dir)
        
        # Test exact match
        assert discovery.find_mode_by_name("Test Mode") == "test-mode"
        
        # Test case-insensitive match
        assert discovery.find_mode_by_name("test mode") == "test-mode"
        
        # Test partial match
        assert discovery.find_mode_by_name("Special") == "special-mode"
        
        # Test no match
        assert discovery.find_mode_by_name("Nonexistent Mode") is None
    
    def test_get_mode_info(self, temp_modes_dir):
        """Test getting information about a specific mode."""
        # Create test mode
        slug = "test-mode"
        config = self.create_valid_mode_config(slug)
        config["whenToUse"] = "Use this mode for testing"
        self.create_mode_file(temp_modes_dir, slug, config)
        
        discovery = ModeDiscovery(temp_modes_dir)
        
        # Test valid mode
        info = discovery.get_mode_info(slug)
        assert info is not None
        assert info["slug"] == slug
        assert info["name"] == config["name"]
        assert info["roleDefinition"] == config["roleDefinition"]
        assert info["whenToUse"] == config["whenToUse"]
        assert info["category"] == "discovered"  # Based on categorization rules
        
        # Test invalid mode
        assert discovery.get_mode_info("nonexistent-mode") is None