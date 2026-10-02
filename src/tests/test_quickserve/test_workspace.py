"""
Tests the workspace

Author: Quintin Dunn
Date: 10/02/2026
"""

import unittest
import uuid
from pathlib import Path

from tempfile import TemporaryDirectory

from QuickServe.FileSystem.path_resolver import Workspace

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class TestWorkspace(unittest.TestCase):
    """
    Tests the workspace class
    """

    def setUp(self):
        """
        Sets up the workspace for tests
        """

        self.worked = False
        self.tmp = TemporaryDirectory()
        self.cwd = Path(self.tmp.name).resolve().absolute()
        self.workspace = Workspace(root=self.cwd)

    def tearDown(self):
        """
        Deletes the temp directory, and setups a new one.
        """

        self.tmp.cleanup()
        self.cwd = Path(self.tmp.name).resolve().absolute()

    def test_ensure_directory(self):
        """
        Tests ensuring relative directory.
        """

        self.workspace.ensure_directory("tests")
        self.assertTrue((self.cwd / "tests").exists())

    def test_ensure_directory_absolute(self):
        """
        Tests ensuring absolute directory.
        """

        with TemporaryDirectory() as tmp:
            tmp = Path(tmp).absolute()
            self.workspace.ensure_directory(tmp / "test")
            self.assertTrue((tmp / "test").exists())

    def call_if_not_exist_callback(self):
        """
        Sets self.worked to True as a callback to test Workspace.call_if_not_exists
        """

        self.worked = True

    def test_call_if_not_exist_relative(self):
        """
        Tests the Workspace.call_if_not_exist function on a relative path
        """

        self.workspace.call_if_not_exist("foo", self.call_if_not_exist_callback)
        self.assertTrue(self.worked)

    def test_call_if_not_exist_absolute(self):
        """
        Tests the Workspace.call_if_not_exist function on an absolute path
        """

        self.workspace.call_if_not_exist(
            Path.home() / str(uuid.uuid4()), self.call_if_not_exist_callback
        )
        self.assertTrue(self.worked)

    def test_call_if_not_exist_exists(self):
        """
        Tests the Workspace.call_if_not_exist function on an existing path
        """

        self.workspace.call_if_not_exist(__file__, self.call_if_not_exist_callback)
        self.assertFalse(self.worked)

    def test_get_path_absolute(self):
        """
        Tests getting an absolute path
        """

        path = self.cwd / "test.txt"

        result = self.workspace.get_path(path)

        self.assertEqual(result, path)

    def test_get_path_relative(self):
        """
        Tests getting a relative path
        """

        path = Path("test.txt")

        result = self.workspace.get_path(path)

        self.assertEqual(result, self.cwd / path)

    def test_get_path_relative_directory(self):
        """
        Tests getting a path relative to another directory
        """

        path = Path("modules/test")

        result = self.workspace.get_path(path)

        self.assertEqual(result, self.cwd / path)
