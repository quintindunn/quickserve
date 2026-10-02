"""
Tests the runtime manager

Author: Quintin Dunn
Date: 10/01/2026
"""

import subprocess
import unittest
from pathlib import Path

from tempfile import TemporaryDirectory
from unittest.mock import patch

from QuickServe.FileSystem.path_resolver import Workspace
from QuickServe.Runtimes.runtime_manager import RuntimeManager

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class TestRuntimes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Sets the cwd attribute
        """
        cls.cwd = None

    def tearDown(self):
        """
        Makes sure to remove any CWD.
        """
        self.cwd.cleanup()

    @patch("QuickServe.FileSystem.path_resolver.platform.system")
    def test_get_jre_linux(self, mock_system):
        """
        Tests getting the JRE for linux
        """

        self.cwd = TemporaryDirectory()
        mock_system.return_value = "Linux"

        workspace = Workspace(root=Path(self.cwd.name))
        runtime = RuntimeManager(workspace=workspace)

        runtime.ensure_jre(8, "jre")
        executable = runtime.get_java_executable(8, "jre", False)
        expected_path = (
            Path(self.cwd.name) / "runtimes" / "jre" / "8-jre" / "bin" / "java"
        )
        self.assertEqual(executable, expected_path)
        self.assertTrue(executable.exists())

    @patch("QuickServe.FileSystem.path_resolver.platform.system")
    def test_get_jre_windows(self, mock_system):
        """
        Tests getting the JRE for windows
        *NOTE: Not implemented*
        """

        self.cwd = TemporaryDirectory()
        mock_system.return_value = "Windows"

        workspace = Workspace(root=Path(self.cwd.name))
        runtime = RuntimeManager(workspace=workspace)

        with self.assertRaises(NotImplementedError):
            runtime.ensure_jre(8, "jre")

        # runtime.ensure_jre(8, "jre")
        # executable = runtime.get_java_executable(8, "jre", False)
        # expected_path = Path(self.cwd.name) / "runtimes" / "jre" / "8-jre" / "bin" / "java"
        # self.assertEqual(executable, expected_path)
        # self.assertTrue(executable.exists())

    @patch("QuickServe.FileSystem.path_resolver.platform.system")
    def test_get_jre_darwin(self, mock_system):
        """
        Tests getting the JRE for darwin
        :return:
        """

        self.cwd = TemporaryDirectory()
        mock_system.return_value = "Darwin"

        workspace = Workspace(root=Path(self.cwd.name))
        runtime = RuntimeManager(workspace=workspace)

        runtime.ensure_jre(8, "jre")
        executable = runtime.get_java_executable(8, "jre", False)
        expected_path = (
            Path(self.cwd.name) / "runtimes" / "jre" / "8-jre" / "bin" / "java"
        )
        self.assertEqual(executable, expected_path)
        self.assertTrue(executable.exists())

    def test_jre(self):
        """
        Tests that the JRE installation works *NOTE: ONLY TESTS IN HOST MACHINES OS*
        """
        self.cwd = TemporaryDirectory()

        workspace = Workspace(root=Path(self.cwd.name))
        runtime = RuntimeManager(workspace=workspace)
        executable = runtime.get_java_executable(8, "jre", True)
        command = [executable.resolve().absolute(), "-version"]
        result = subprocess.run(command)

        self.assertEqual(result.returncode, 0)
