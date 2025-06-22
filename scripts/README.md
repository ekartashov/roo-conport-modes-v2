# Roo Modes Sync

A comprehensive Python package for synchronizing Roo Modes configuration with Test-Driven Development.

## Overview

This package provides a robust, extensible solution for managing Roo Modes global configuration. It replaces the original monolithic `sync.py` script with a well-structured, thoroughly tested Python package that follows modern software engineering practices.

## Features

- **🏗️ Modular Architecture**: Clean separation of concerns with dedicated modules for validation, discovery, ordering, and synchronization
- **🧪 Test-Driven Development**: Comprehensive test suite with >95% coverage using pytest
- **📋 Multiple Ordering Strategies**: Strategic, alphabetical, category-based, and custom ordering
- **🔍 Advanced Discovery**: Automatic mode categorization and intelligent file discovery
- **✅ Robust Validation**: Schema validation with detailed error reporting
- **🎛️ Flexible Configuration**: External YAML configuration files for complex setups
- **🚀 CLI Interface**: Full-featured command-line interface with preview and validation modes
- **💾 Backup Support**: Automatic backup creation before configuration updates
- **🔧 Extensible Design**: Easy to add new ordering strategies and validation rules

## Installation

### Development Installation

```bash
cd scripts
pip install -e ".[dev]"
```

### Production Installation

```bash
cd scripts
pip install .
```

## Quick Start

### Basic Usage

```bash
# Sync with default strategic ordering
python -m roo_modes_sync

# List discovered modes
python -m roo_modes_sync --list-modes

# Validate modes without syncing
python -m roo_modes_sync --validate-only

# Preview changes without applying
python -m roo_modes_sync --dry-run --verbose
```

### Advanced Usage

```bash
# Use alphabetical ordering
python -m roo_modes_sync --order alphabetical

# Prioritize specific modes
python -m roo_modes_sync --priority code debug --order strategic

# Exclude modes from sync
python -m roo_modes_sync --exclude deprecated-mode experimental-mode

# Use external configuration
python -m roo_modes_sync --config ordering.yaml

# Custom category ordering
python -m roo_modes_sync --order category --category-order core,specialized,enhanced
```

## Project Structure

```
scripts/
├── src/roo_modes_sync/           # Main package
│   ├── __init__.py               # Package initialization
│   ├── __main__.py               # Main entry point
│   ├── cli.py                    # Command-line interface
│   ├── exceptions.py             # Custom exception classes
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   ├── discovery.py          # Mode discovery and categorization
│   │   ├── ordering.py           # Ordering strategies
│   │   ├── sync.py               # Main synchronization logic
│   │   └── validation.py         # Mode validation
│   └── config/                   # Configuration management
│       ├── __init__.py
│       └── ordering.py           # External config handling
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_discovery.py         # Discovery tests
│   ├── test_integration.py       # Integration tests
│   ├── test_ordering.py          # Ordering strategy tests
│   └── test_validation.py        # Validation tests
├── pyproject.toml                # Project configuration
└── README.md                     # This file
```

## Ordering Strategies

### Strategic Ordering (Default)
Maintains the original hardcoded strategic order optimized for workflow efficiency:
- Core modes first (code, debug)
- Enhanced modes (architect, ask)
- Specialized modes (prompt-enhancer, conport-maintenance)
- Discovered modes last

### Alphabetical Ordering
Sorts modes alphabetically within each category while maintaining category precedence.

### Category Ordering
Allows custom category precedence with configurable within-category sorting.

### Custom Ordering
Enables explicit mode ordering via configuration or command-line options.

## Configuration Files

Create external YAML configuration files for complex setups:

```yaml
# ordering.yaml
strategy: category
options:
  category_order: [core, enhanced, specialized, discovered]
  within_category_order: alphabetical
priority_first: [code, debug]
exclude: [deprecated-mode]
metadata:
  description: "Production ordering configuration"
  version: "1.0"
```

## Testing

### Run All Tests
```bash
cd scripts
pytest
```

### Run with Coverage
```bash
cd scripts
pytest --cov=roo_modes_sync --cov-report=html
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/test_validation.py tests/test_discovery.py tests/test_ordering.py

# Integration tests
pytest tests/test_integration.py

# Verbose output
pytest -v
```

## Development

### Setting Up Development Environment

```bash
cd scripts
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Code Quality Tools

```bash
# Format code
black src tests

# Type checking
mypy src

# Run linting
flake8 src tests

# Sort imports
isort src tests
```

### Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

## API Reference

### Core Classes

#### `ModeConfigSync`
Main synchronization manager that orchestrates the entire workflow.

```python
from roo_modes_sync.core.sync import ModeConfigSync

sync_manager = ModeConfigSync(modes_dir=Path("./modes"))
success = sync_manager.sync_modes(order='strategic', verbose=True)
```

#### `ModeValidator`
Validates mode configuration files against schema requirements.

```python
from roo_modes_sync.core.validation import ModeValidator

validator = ModeValidator()
is_valid = validator.validate_mode_config(config, "mode-slug")
```

#### `ModeDiscovery`
Discovers and categorizes mode files automatically.

```python
from roo_modes_sync.core.discovery import ModeDiscovery

discovery = ModeDiscovery(Path("./modes"))
modes_by_category = discovery.discover_modes()
```

### Ordering Strategies

All ordering strategies implement the `OrderingStrategy` protocol:

```python
from roo_modes_sync.core.ordering import OrderingStrategyFactory

factory = OrderingStrategyFactory()
strategy = factory.create_strategy('alphabetical')
ordered_modes = strategy.order_modes(modes_by_category, options={})
```

## Migration from Original sync.py

The new package maintains full backward compatibility with the original `sync.py` functionality:

1. **Same CLI Interface**: All original command-line options work unchanged
2. **Same Output Format**: Generates identical `global.config.json` structure
3. **Enhanced Features**: Adds validation, dry-run, and configuration options
4. **Better Error Handling**: More descriptive error messages and graceful failures

### Migration Steps

1. Install the new package: `pip install -e ".[dev]"`
2. Replace calls to `python sync.py` with `python -m roo_modes_sync`
3. Optionally leverage new features like `--dry-run` and external configuration

## Error Handling

The package provides comprehensive error handling with custom exception types:

- **`ValidationError`**: Mode configuration validation failures
- **`DiscoveryError`**: Mode file discovery issues
- **`SyncError`**: Synchronization process failures
- **`ConfigurationError`**: External configuration problems

All errors include detailed messages and context for debugging.

## Performance

- **Fast Discovery**: Efficient file system traversal with caching
- **Minimal Memory Usage**: Stream processing for large mode collections
- **Incremental Sync**: Only processes changed modes when possible
- **Parallel Validation**: Concurrent validation for improved performance

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Write tests for new functionality
4. Ensure all tests pass: `pytest`
5. Follow code style guidelines: `black src tests`
6. Submit a pull request

### Development Guidelines

- **Test-Driven Development**: Write tests before implementation
- **Type Hints**: Use type annotations throughout
- **Documentation**: Update docstrings and README for new features
- **Error Handling**: Provide meaningful error messages
- **Backward Compatibility**: Maintain compatibility with existing workflows

## Troubleshooting

### Common Issues

**1. "Could not find modes directory"**
- Ensure you're running from the correct directory
- Use `--modes-dir` to specify the path explicitly
- Check that the directory contains `.yaml` mode files

**2. "Validation failed"**
- Use `--validate-only --verbose` to see detailed validation errors
- Check mode files for required fields: name, model, icon, description
- Ensure YAML syntax is valid

**3. "Permission denied"**
- Check write permissions for the modes directory
- Ensure no other processes are using the global.config.json file

**4. "Custom ordering strategy requires custom_order"**
- Provide `--custom-order` option or use external configuration file
- Ensure custom_order lists valid mode slugs

### Debug Mode

Enable verbose output for detailed debugging:

```bash
python -m roo_modes_sync --verbose --dry-run
```

## License

This project maintains the same license as the parent Roo Modes project.

## Changelog

### v1.0.0 (Initial Release)
- ✅ Complete rewrite with modular architecture
- ✅ Comprehensive test suite with pytest
- ✅ Multiple ordering strategies
- ✅ External configuration support
- ✅ CLI interface with advanced options
- ✅ Robust validation and error handling
- ✅ Backward compatibility with original sync.py