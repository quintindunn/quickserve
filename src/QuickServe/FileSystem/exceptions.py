"""
Exceptions for the file system.

Author: Quintin Dunn
Date: 09/09/2026
"""


class InvalidModuleError(Exception):
    """
    Exception raised when a module fails validation
    """

class UnsupportedModuleError(Exception):
    """
    Exception raised when a module is not supported.
    """


class AssetDoesntExist(Exception):
    """
    Exception raised when an asset trying to be loaded isn't found.
    """
