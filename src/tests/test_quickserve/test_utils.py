"""
Tests Quickserve.Driver.utils

Author: Quintin Dunn
Date: 10/01/2026
"""

import unittest

from QuickServe.Driver.utils import sanitize_filename

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class TestSanitizeFilename(unittest.TestCase):
    """
    Tests file name sanitizer
    """

    def test_valid_filename(self):
        """
        Tests that a valid filename isn't sanitized
        """

        self.assertEqual(sanitize_filename("hello-world_123"), "hello-world_123")

    def test_replaces_invalid_characters(self):
        """
        Tests that illegal characters get replaced.
        """

        self.assertEqual(sanitize_filename("hello world.txt"), "hello_world_txt")

    def test_replaces_multiple_invalid_characters(self):
        """
        Tests multiple illegal characters get replaced.
        """

        self.assertEqual(sanitize_filename("hello!@#$%^&*()"), "hello__________")

    def test_truncates_to_250_characters(self):
        """
        Tests that files with a filename > 250 characters get truncated.
        """

        filename = "a" * 300

        sanitized = sanitize_filename(filename)

        self.assertEqual(len(sanitized), 250)
        self.assertEqual(sanitized, "a" * 250)

    def test_empty_string(self):
        """
        Tests empty strings remain empty strings.
        """

        self.assertEqual(sanitize_filename(""), "")
