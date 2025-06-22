#!/usr/bin/env python3
"""
Custom exceptions for the Roo Modes Sync package.
"""


class RooModesSyncError(Exception):
    """Base exception for all errors in the package."""
    pass


class ValidationError(RooModesSyncError):
    """Exception raised for mode configuration validation errors."""
    pass


class ModeValidationError(ValidationError):
    """Exception raised for specific mode configuration validation errors."""
    pass


class DiscoveryError(RooModesSyncError):
    """Exception raised for mode discovery errors."""
    pass


class SyncError(RooModesSyncError):
    """Exception raised for synchronization process errors."""
    pass


class ConfigurationError(RooModesSyncError):
    """Exception raised for configuration loading or parsing errors."""
    pass