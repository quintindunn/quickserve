import os.path
import shutil
import unittest
from tempfile import TemporaryDirectory

from pathlib import Path

from QuickServe.FileSystem.path_resolver import Workspace
from tests.fake import ModulesDir

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

    def test_placeholder(self):
        pass