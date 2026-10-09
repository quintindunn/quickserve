"""
Tests the BaseInstance class.

Author: Quintin Dunn
Date: 10/08/2026
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from unittest.mock import MagicMock

from QuickServe.Driver.instance.base_instance import BaseInstance
from QuickServe.FileSystem.path_resolver import Workspace


class TestBaseInstance(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.workspace = Workspace(Path(self.temp_dir.name) / "workspace")
        self.instance_uuid = uuid4()

        self.instance = BaseInstance(
            base_module=MagicMock(),
            instance_name="Test Instance",
            uuid=self.instance_uuid,
            module_name="test_module",
            workspace=self.workspace,
        )

    def test_working_directory(self):
        """Test that working_directory creates the expected instance directory."""

        result = self.instance.working_directory()

        expected_name = f"{self.instance_uuid.hex[:16]}-Test_Instance"
        expected_path = self.workspace.root / "instances" / expected_name

        self.assertEqual(result, expected_path)
        self.assertTrue(result.is_dir())
