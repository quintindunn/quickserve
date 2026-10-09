"""
Tests the BaseModule class

Author: Quintin Dunn
Date: 10/03/2026
"""

import importlib
import logging
import sys
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from QuickServe.FileSystem.exceptions import InvalidModuleError, AssetDoesntExist
from QuickServe.FileSystem.modules import BaseModule
from QuickServe.FileSystem.path_resolver import Workspace
from tests.fake.module_dir import setup_modules

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class TestBaseModule(unittest.TestCase):
    """
    Tests the BaseModule class.
    """

    def setUp(self):
        """
        Sets up a workspace for each test
        """
        self.cwd = TemporaryDirectory()
        self.workspace = Workspace(Path(self.cwd.name) / "workspace")

    def tearDown(self):
        """
        Resets the workspace
        """

        # These two lines made me suffer, without them, I guess Python caches the imports?
        sys.modules.pop("mymodule", None)
        importlib.invalidate_caches()

        self.cwd.cleanup()

    def test_valid_module(self):
        """
        Tests a valid module that should load.
        """

        module_path = setup_modules(self.workspace)

        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
        )

        module.load_module()

    def test_missing_module_name(self):
        """
        Tests that a module missing its name throws an error.
        """

        module_path = setup_modules(self.workspace)
        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
            remove_attr_on_load="NAME",
        )

        with self.assertRaises(InvalidModuleError):
            module.load_module()

    def test_missing_version(self):
        """
        Tests that a module missing its version throws an error.
        """

        module_path = setup_modules(self.workspace)
        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
            remove_attr_on_load="VERSION",
        )

        with self.assertRaises(InvalidModuleError):
            module.load_module()

    def test_missing_quickserve_version(self):
        """
        Tests that a module missing the quickserve version throws an error.
        """

        module_path = setup_modules(self.workspace)
        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
            remove_attr_on_load="QUICKSERVE_VERSION",
        )

        with self.assertRaises(InvalidModuleError):
            module.load_module()

    def test_missing_pages(self):
        """
        Tests that a module missing a list of pages throws an error.
        """

        module_path = setup_modules(self.workspace)
        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
            remove_attr_on_load="PAGES",
        )

        with self.assertRaises(InvalidModuleError):
            module.load_module()

    def test_get_resource(self):
        """
        Tests getting a valid resource within the module's path.
        """

        module_path = setup_modules(self.workspace)
        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
        )

        create_path = module.get_resource_path("create.html")
        self.assertEqual(
            create_path,
            self.workspace.get_path(
                Path("modules") / "mymodule" / "resources" / "create.html"
            ),
        )

    def test_get_missing_resource(self):
        """
        Tests getting a non-existent resource within the module throws an error.
        """

        module_path = setup_modules(self.workspace)
        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
        )

        with self.assertRaises(AssetDoesntExist):
            module.get_resource_path("fake_asset.html")
