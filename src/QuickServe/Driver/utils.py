"""
Utility functions for the main driver.

Author: Quintin Dunn
Date: 09/09/2026
"""

import logging
import re

logger = logging.getLogger("Driver.utils")


def sanitize_filename(string: str) -> str:
    """
    Converts a string to a sanitized filename.

    :param string: The input filename
    :return: a sanitize filename.
    """
    replacement_pattern = re.compile(r"[^a-zA-Z0-9-_]")
    sanitized = re.sub(replacement_pattern, "_", string)[:250]
    logger.debug(f"Sanitized file: {string} -> {sanitized}")
    return sanitized
