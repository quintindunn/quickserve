import unittest

from QuickServe.Driver.utils import sanitize_filename


class TestSanitizeFilename(unittest.TestCase):
    def test_valid_filename(self):
        self.assertEqual(
            sanitize_filename("hello-world_123"),
            "hello-world_123"
        )

    def test_replaces_invalid_characters(self):
        self.assertEqual(
            sanitize_filename("hello world.txt"),
            "hello_world_txt"
        )

    def test_replaces_multiple_invalid_characters(self):
        self.assertEqual(
            sanitize_filename("hello!@#$%^&*()"),
            "hello__________"
        )

    def test_allows_hyphens_and_underscores(self):
        self.assertEqual(
            sanitize_filename("hello-world_test"),
            "hello-world_test"
        )

    def test_replaces_unicode_characters(self):
        self.assertEqual(
            sanitize_filename("café-日本"),
            "caf_-__"
        )

    def test_truncates_to_250_characters(self):
        filename = "a" * 300

        sanitized = sanitize_filename(filename)

        self.assertEqual(len(sanitized), 250)
        self.assertEqual(sanitized, "a" * 250)

    def test_empty_string(self):
        self.assertEqual(
            sanitize_filename(""),
            ""
        )
