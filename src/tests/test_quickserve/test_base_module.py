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
from unittest.mock import patch

from QuickServe.FileSystem.exceptions import (
    InvalidModuleError,
    AssetDoesntExist,
    UnsupportedModuleError,
)
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
            config=None,  # noqa
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
            config=None,  # noqa
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
            config=None,  # noqa
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
            config=None,  # noqa
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
            config=None,  # noqa
        )

        with self.assertRaises(InvalidModuleError):
            module.load_module()

    def test_plugin_supported_os(self):
        module_path = setup_modules(self.workspace)

        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
            config=None,  # noqa
        )
        module.load_module()

    def test_plugin_no_supported_os_attr(self):
        module_path = setup_modules(self.workspace)

        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
            remove_attr_on_load="SUPPORTED_OPERATING_SYSTEMS",
            config=None,  # noqa
        )
        with self.assertRaises(InvalidModuleError):
            module.load_module()

    def test_plugin_unsupported_os(self):
        module_path = setup_modules(self.workspace)

        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
            config=None,  # noqa
        )

        with patch(
            "QuickServe.FileSystem.modules.platform.system",
            return_value="unsupported_os",
        ):
            with self.assertRaises(UnsupportedModuleError):
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
            config=None,  # noqa
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
            config=None,  # noqa
        )

        with self.assertRaises(AssetDoesntExist):
            module.get_resource_path("fake_asset.html")
