#!/usr/bin/env python3
"""
Test runner for roo_modes_sync package.

This script runs pytest on the package's test directory, properly setting up the Python path
to ensure imports work correctly. It can run all tests or specific test files as specified
by command line arguments.

Usage:
    python run_tests.py [test_file1.py [test_file2.py ...]]
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Run the test suite with proper path setup."""
    # Get the root directory of the package
    package_dir = Path(__file__).parent.absolute()
    tests_dir = package_dir / "tests"
    
    # Check if tests directory exists
    if not tests_dir.exists():
        print(f"Error: Tests directory not found at {tests_dir}")
        return 1

    # Add parent directory of package to sys.path to make the package importable
    # This is needed because we want to test the installed package
    scripts_dir = package_dir.parent
    
    # Print diagnostic info
    print(f"Running tests from: {tests_dir}")
    print(f"Package directory: {scripts_dir}")
    
    # Get test files to run from command line arguments
    test_paths = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Construct the pytest command
    pytest_command = ["pytest"]
    
    # Add test files if specified, otherwise run all tests
    if test_paths:
        for test_path in test_paths:
            # Make sure paths are relative to the current directory
            test_file = Path(test_path)
            if not test_file.is_absolute():
                test_file = tests_dir / test_file
            pytest_command.append(str(test_file))
    else:
        pytest_command.append(str(tests_dir))
    
    # Add verbosity flag
    pytest_command.append("-v")
    
    # Update Python path for the subprocess
    env = os.environ.copy()
    python_path = [str(scripts_dir)]
    if 'PYTHONPATH' in env:
        python_path.append(env['PYTHONPATH'])
    env['PYTHONPATH'] = os.pathsep.join(python_path)
    
    # Print Python path for debugging
    print(f"Python path: {python_path}")
    
    # Run pytest
    return subprocess.call(pytest_command, env=env)


if __name__ == "__main__":
    sys.exit(main())