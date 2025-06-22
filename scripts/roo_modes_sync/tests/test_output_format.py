#!/usr/bin/env python3
"""
Test output format matches the required template structure.
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path

try:
    from ..core.sync import ModeSync
except ImportError:
    import sys
    from pathlib import Path
    script_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(script_dir / "core"))
    
    from core.sync import ModeSync


class TestOutputFormat:
    """Test that output format matches the required template structure."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.modes_dir = self.temp_dir / "modes"
        self.output_dir = self.temp_dir / "output"
        
        # Create directories
        self.modes_dir.mkdir(parents=True)
        self.output_dir.mkdir(parents=True)
        
        # Create test mode files with proper structure
        self.create_test_mode("security-auditor", "🛡️ Security Auditor", [
            "Follow this structured approach:",
            "1. ANALYSIS PHASE:",
            "   - Review the entire codebase systematically",
            "   - Focus on critical areas: authentication, data handling",
            "2. PLANNING PHASE:",
            "   - For each identified vulnerability:",
            "     - Explain the exact nature of the security risk"
        ])
        
        self.create_test_mode("debate-opponent", "👎🏽 Debate Opponent", [
            "You are a debate agent focused on critiquing the Proponent's argument.",
            "Critique the Proponent's latest argument and provide one counterargument."
        ])

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def create_test_mode(self, slug, name, instructions_lines):
        """Create a test mode file."""
        mode_file = self.modes_dir / f"{slug}.yaml"
        
        # Properly indent instructions for YAML
        indented_instructions = []
        for line in instructions_lines:
            if line.strip():
                indented_instructions.append(f"  {line}")
            else:
                indented_instructions.append("")
        instructions = "\n".join(indented_instructions)
        
        content = f"""slug: {slug}
name: {name}
roleDefinition: Act as an expert {slug.replace('-', ' ')} conducting thorough analysis.
whenToUse: >-
  Activate this mode when you need to perform {slug.replace('-', ' ')} tasks.
customInstructions: |-
{instructions}
groups:
  - read
  - command
source: global"""
        
        mode_file.write_text(content)

    def test_output_format_structure(self):
        """Test that output format matches required structure."""
        sync = ModeSync(self.modes_dir)
        output_file = self.output_dir / "custom_modes.yaml"
        sync.set_global_config_path(output_file)
        
        # Generate config
        result = sync.sync_modes(strategy_name='alphabetical', options={})
        assert result is True
        
        # Read generated file
        assert output_file.exists()
        content = output_file.read_text()
        
        # Parse YAML to verify structure
        config = yaml.safe_load(content)
        
        # Verify top-level structure
        assert "customModes" in config
        assert isinstance(config["customModes"], list)
        assert len(config["customModes"]) > 0

    def test_mode_entry_structure(self):
        """Test that each mode entry has correct structure."""
        sync = ModeSync(self.modes_dir)
        output_file = self.output_dir / "custom_modes.yaml"
        sync.set_global_config_path(output_file)
        
        # Generate config
        sync.sync_modes(strategy_name='alphabetical', options={})
        
        # Parse generated file
        config = yaml.safe_load(output_file.read_text())
        
        # Check first mode structure
        mode = config["customModes"][0]
        
        # Required fields
        assert "slug" in mode
        assert "name" in mode
        assert "roleDefinition" in mode
        assert "customInstructions" in mode
        assert "groups" in mode
        assert "source" in mode
        
        # Verify types
        assert isinstance(mode["slug"], str)
        assert isinstance(mode["name"], str)
        assert isinstance(mode["roleDefinition"], str)
        assert isinstance(mode["customInstructions"], str)
        assert isinstance(mode["groups"], list)
        assert isinstance(mode["source"], str)
        assert mode["source"] == "global"

    def test_multiline_string_formatting(self):
        """Test that multiline strings are properly formatted."""
        sync = ModeSync(self.modes_dir)
        output_file = self.output_dir / "custom_modes.yaml"
        sync.set_global_config_path(output_file)
        
        # Generate config
        sync.sync_modes(strategy_name='alphabetical', options={})
        
        # Read raw content to check formatting
        content = output_file.read_text()
        
        # Check that multiline strings use proper YAML syntax
        # Should use >- for folded scalars or proper indentation
        lines = content.split('\n')
        
        # Find roleDefinition and customInstructions lines
        role_def_lines = [i for i, line in enumerate(lines) if 'roleDefinition:' in line]
        custom_instr_lines = [i for i, line in enumerate(lines) if 'customInstructions:' in line]
        
        assert len(role_def_lines) > 0
        assert len(custom_instr_lines) > 0
        
        # Verify multiline content is properly formatted
        for line_idx in role_def_lines + custom_instr_lines:
            line = lines[line_idx]
            # Should either be on same line or use >- syntax
            assert ':' in line
            if line.strip().endswith(':'):
                # Next line should be indented content or >-
                next_line = lines[line_idx + 1] if line_idx + 1 < len(lines) else ""
                assert next_line.startswith('    ') or next_line.strip().startswith('>')

    def test_groups_array_formatting(self):
        """Test that groups array is properly formatted."""
        sync = ModeSync(self.modes_dir)
        output_file = self.output_dir / "custom_modes.yaml"
        sync.set_global_config_path(output_file)
        
        # Generate config
        sync.sync_modes(strategy_name='alphabetical', options={})
        
        # Parse generated file
        config = yaml.safe_load(output_file.read_text())
        
        # Check groups formatting
        for mode in config["customModes"]:
            groups = mode["groups"]
            assert isinstance(groups, list)
            assert len(groups) > 0
            
            # Each group should be a string or complex group structure
            for group in groups:
                assert isinstance(group, (str, list))

    def test_no_template_content_in_output(self):
        """Test that template content is not included in output."""
        sync = ModeSync(self.modes_dir)
        output_file = self.output_dir / "custom_modes.yaml"
        sync.set_global_config_path(output_file)
        
        # Generate config
        sync.sync_modes(strategy_name='alphabetical', options={})
        
        # Read generated content
        content = output_file.read_text()
        
        # Should not contain template markers
        assert "your-mode-name" not in content
        assert "🔧 Your Mode Display Name" not in content
        assert "# Copy this template" not in content
        assert "# Basic Mode Template" not in content

    def test_clean_yaml_structure(self):
        """Test that generated YAML has clean structure without extra metadata."""
        sync = ModeSync(self.modes_dir)
        output_file = self.output_dir / "custom_modes.yaml"
        sync.set_global_config_path(output_file)
        
        # Generate config
        sync.sync_modes(strategy_name='alphabetical', options={})
        
        # Parse generated file
        config = yaml.safe_load(output_file.read_text())
        
        # Check that only expected fields are present
        expected_top_level = {"customModes"}
        assert set(config.keys()) == expected_top_level
        
        # Check mode fields
        expected_mode_fields = {"slug", "name", "roleDefinition", "customInstructions", "groups", "source"}
        for mode in config["customModes"]:
            mode_fields = set(mode.keys())
            # Should have at least required fields, may have optional ones like whenToUse
            assert expected_mode_fields.issubset(mode_fields)
            
            # Should not have development metadata
            dev_fields = {"metadata", "dev_notes", "template", "example"}
            assert not any(field in mode_fields for field in dev_fields)

    def test_alphabetical_ordering(self):
        """Test that modes are ordered alphabetically by slug."""
        sync = ModeSync(self.modes_dir)
        output_file = self.output_dir / "custom_modes.yaml"
        sync.set_global_config_path(output_file)
        
        # Generate config with alphabetical strategy
        sync.sync_modes(strategy_name='alphabetical', options={})
        
        # Parse generated file
        config = yaml.safe_load(output_file.read_text())
        
        # Check ordering
        slugs = [mode["slug"] for mode in config["customModes"]]
        assert slugs == sorted(slugs), f"Modes not in alphabetical order: {slugs}"

    def test_template_format_compliance(self):
        """Test that output format complies with the template structure."""
        sync = ModeSync(self.modes_dir)
        output_file = self.output_dir / "custom_modes.yaml"
        sync.set_global_config_path(output_file)
        
        # Generate config
        sync.sync_modes(strategy_name='alphabetical', options={})
        
        # Read content
        content = output_file.read_text()
        lines = content.split('\n')
        
        # Should start with customModes:
        assert lines[0] == "customModes:"
        
        # Should have proper indentation (2 spaces for list items, 4 for properties)
        mode_started = False
        for line in lines[1:]:
            if line.strip().startswith('- slug:'):
                mode_started = True
                assert line.startswith('  - ')  # 2-space indent for list item
            elif mode_started and line.strip() and not line.startswith('  - '):
                if ':' in line and not line.strip().startswith('#'):
                    assert line.startswith('    ')  # 4-space indent for properties