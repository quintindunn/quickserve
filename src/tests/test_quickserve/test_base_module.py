import importlib
import logging
import sys
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from QuickServe.FileSystem.exceptions import InvalidModuleError
from QuickServe.FileSystem.modules import BaseModule
from QuickServe.FileSystem.path_resolver import Workspace
from tests.fake.module_dir import setup_modules

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class TestBaseModule(unittest.TestCase):
    def setUp(self):
        self.cwd = TemporaryDirectory()
        self.workspace = Workspace(Path(self.cwd.name) / "workspace")

    def tearDown(self):
        sys.modules.pop("mymodule", None)
        importlib.invalidate_caches()
        self.cwd.cleanup()

    def test_valid_module(self):
        module_path = setup_modules(self.workspace)

        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None  # noqa
        )

        module.load_module()

    def test_missing_module_name(self):
        module_path = setup_modules(self.workspace)
        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
            remove_attr_on_load="NAME"
        )

        with self.assertRaises(InvalidModuleError):
            module.load_module()

    def test_missing_version(self):
        module_path = setup_modules(self.workspace)
        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
            remove_attr_on_load="VERSION"
        )

        with self.assertRaises(InvalidModuleError):
            module.load_module()

    def test_missing_quickserve_version(self):
        module_path = setup_modules(self.workspace)
        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
            remove_attr_on_load="QUICKSERVE_VERSION"
        )

        with self.assertRaises(InvalidModuleError):
            module.load_module()

    def test_missing_pages(self):
        module_path = setup_modules(self.workspace)
        module = BaseModule(
            module_path=module_path,
            workspace=self.workspace,
            runtime_manager=None,  # noqa
            remove_attr_on_load="PAGES"
        )

        with self.assertRaises(InvalidModuleError):
            module.load_module()