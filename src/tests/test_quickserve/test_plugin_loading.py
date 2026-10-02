import logging
import os.path
import shutil
import sys
import unittest
from tempfile import TemporaryDirectory

from pathlib import Path

from QuickServe.FileSystem.path_resolver import Workspace
from QuickServe.FileSystem.plugins import PluginLoader

from tests.fake.module_dir import setup_modules

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class TestPluginLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Creates a workspace for initializing the Config
        """

        cls.cwd = TemporaryDirectory()
        cls.workspace = Workspace(Path(cls.cwd.name) / "workspace")

    def tearDown(self):
        for file in os.listdir(self.workspace.root):
            file_path = self.workspace.get_path(file)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    def test_plugin_loader_load_all(self):
        setup_modules(self.workspace)

        plugin_loader = PluginLoader(workspace=self.workspace, runtime_manager=None)
        catalog = plugin_loader.load_all()
        self.assertEqual(len(list(catalog.items())), 1)

    def test_plugin_loader_no_modules(self):
        plugin_loader = PluginLoader(workspace=self.workspace, runtime_manager=None)
        catalog = plugin_loader.load_all()
        self.assertEqual(len(list(catalog.items())), 0)

    def test_plugin_loader_duplicates(self):
        setup_modules(self.workspace)
        setup_modules(self.workspace, folder_name_modifier="_duplicate")

        with self.assertRaises(ValueError):
            PluginLoader(workspace=self.workspace, runtime_manager=None).load_all()
