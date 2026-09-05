# TESTS GENERATED WITH GENERATIVE AI.

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from QuickServeFS.path_resolver import (
    ROOT_PATH_TABLE,
    Resolver,
    _generate_root,
)


class TestGenerateRoot(unittest.TestCase):
    @patch("QuickServeFS.path_resolver.platform.system")
    def test_linux(self, mock_system):
        mock_system.return_value = "Linux"

        self.assertEqual(
            _generate_root(),
            ROOT_PATH_TABLE["Linux"],
        )

    @patch("QuickServeFS.path_resolver.platform.system")
    def test_darwin(self, mock_system):
        mock_system.return_value = "Darwin"

        self.assertEqual(
            _generate_root(),
            ROOT_PATH_TABLE["Darwin"],
        )

    @patch("QuickServeFS.path_resolver.platform.system")
    def test_windows_not_supported(self, mock_system):
        mock_system.return_value = "Windows"

        with self.assertRaisesRegex(
            NotImplementedError,
            "Windows is currently not supported",
        ):
            _generate_root()

    @patch("QuickServeFS.path_resolver.platform.system")
    def test_unknown_os(self, mock_system):
        mock_system.return_value = "FreeBSD"

        with self.assertRaisesRegex(
            NotImplementedError,
            "OS FreeBSD is not supported",
        ):
            _generate_root()


class TestResolver(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.root = Path(self.temp_dir.name)
        self.resolver = Resolver(self.root)

    def test_explicit_root(self):
        self.assertEqual(
            self.resolver.root,
            self.root,
        )

        self.assertTrue(self.root.exists())
        self.assertTrue(self.root.is_dir())

    def test_get_path_relative(self):
        result = self.resolver.get_path("config.toml")

        self.assertEqual(
            result,
            self.root / "config.toml",
        )

    def test_get_path_nested_relative(self):
        result = self.resolver.get_path("foo/bar.txt")

        self.assertEqual(
            result,
            self.root / "foo" / "bar.txt",
        )

    def test_get_path_absolute(self):
        path = self.root / "somewhere" / "file.txt"

        self.assertEqual(
            self.resolver.get_path(path),
            path,
        )

    def test_get_path_accepts_string(self):
        result = self.resolver.get_path("config.toml")

        self.assertIsInstance(result, Path)

    def test_ensure_directory_absolute(self):
        target = self.root / "nested"

        result = self.resolver._ensure_directory(target)

        self.assertTrue(target.exists())
        self.assertTrue(target.is_dir())
        self.assertEqual(result, target.absolute())

    def test_ensure_directory_relative(self):
        result = self.resolver._ensure_directory("nested")

        target = self.root / "nested"

        self.assertTrue(target.exists())
        self.assertTrue(target.is_dir())
        self.assertEqual(result, target.absolute())

    def test_ensure_directory_idempotent(self):
        self.resolver._ensure_directory("nested")
        self.resolver._ensure_directory("nested")

        self.assertTrue((self.root / "nested").is_dir())

    def test_ensure_file_path_absolute(self):
        path = self.root / "nested" / "config.toml"

        result = self.resolver.ensure_file_path(path)

        self.assertTrue((self.root / "nested").is_dir())
        self.assertEqual(
            result,
            path.absolute(),
        )

    def test_call_if_not_exist_calls_callback(self):
        target = self.root / "missing.txt"

        callback = unittest.mock.Mock()

        self.resolver.call_if_not_exist(
            target,
            callback,
        )

        callback.assert_called_once_with()

    def test_call_if_not_exist_does_not_call_callback(self):
        target = self.root / "existing.txt"
        target.write_text("existing")

        callback = unittest.mock.Mock()

        self.resolver.call_if_not_exist(
            target,
            callback,
        )

        callback.assert_not_called()

    def test_call_if_not_exist_args(self):
        target = self.root / "missing.txt"
        callback = unittest.mock.Mock()

        self.resolver.call_if_not_exist(
            target,
            callback,
            args=["hello", 123],
        )

        callback.assert_called_once_with(
            "hello",
            123,
        )

    def test_call_if_not_exist_kwargs(self):
        target = self.root / "missing.txt"
        callback = unittest.mock.Mock()

        self.resolver.call_if_not_exist(
            target,
            callback,
            kwargs={"value": 123},
        )

        callback.assert_called_once_with(
            value=123,
        )

    def test_call_if_not_exist_args_and_kwargs(self):
        target = self.root / "missing.txt"
        callback = unittest.mock.Mock()

        self.resolver.call_if_not_exist(
            target,
            callback,
            args=["hello"],
            kwargs={"value": 123},
        )

        callback.assert_called_once_with(
            "hello",
            value=123,
        )

    def test_config_property(self):
        self.assertEqual(
            self.resolver.config,
            self.root / "config.yml",
        )


if __name__ == "__main__":
    unittest.main()
