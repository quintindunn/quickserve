"""
Tests the config

Author: Quintin Dunn
Date: 10/02/2026
"""

import os.path
import tomllib
import unittest

from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import BaseModel

from QuickServe.FileSystem.path_resolver import Workspace
from QuickServe.FileSystem.config import Config

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class TestModel(BaseModel):
    """
    Sample PyDantic model for testing Config._get_model
    """

    value: str


class TestConfig(unittest.TestCase):
    """
    Tests the config
    """

    @classmethod
    def setUpClass(cls):
        """
        Creates a workspace for initializing the Config
        """

        cls.cwd = TemporaryDirectory()
        cls.workspace = Workspace(Path(cls.cwd.name) / "workspace")

    def tearDown(self):
        """
        Removes the config.toml between tests
        """

        if os.path.isfile(self.workspace.get_path("config.toml")):
            os.remove(self.workspace.get_path("config.toml"))

    def test_create_default_config(self):
        """
        Tests creating the default config.
        """

        Config(workspace=self.workspace)
        self.assertTrue(self.workspace.get_path("config.toml").exists())
        self.assertGreater(self.workspace.get_path("config.toml").stat().st_size, 0)

    def test_load_config(self):
        """
        Tests loading the config, makes sure it keeps values from the loaded config.
        """

        Config(workspace=self.workspace)
        self.assertTrue(self.workspace.get_path("config.toml").exists())

        with open(self.workspace.get_path("config.toml"), "r") as f:
            raw = f.read()

        raw = raw.replace(
            "secret-key-change-in-production", "changed-secret-key-not-for-prod"
        )
        with open(self.workspace.get_path("config.toml"), "w") as f:
            f.write(raw)

        config = Config(workspace=self.workspace)
        self.assertEqual(config.web.secret_key, "changed-secret-key-not-for-prod")

    def test_invalid_config(self):
        """
        Tests that an invalid config raises an error.
        """

        with open(self.workspace.get_path("config.toml"), "w") as f:
            f.write("162f8d6b0b8abb61a633abd67fc3619e")

        with self.assertRaises(tomllib.TOMLDecodeError):
            Config(workspace=self.workspace)

    def test_invalid_type(self):
        """
        Tests that an error is thrown if the config has an invalid type.
        """

        Config(workspace=self.workspace)
        self.assertTrue(self.workspace.get_path("config.toml").exists())

        with open(self.workspace.get_path("config.toml"), "r") as f:
            raw = f.read()

        raw = raw.replace('"secret-key-change-in-production"', "5")
        with open(self.workspace.get_path("config.toml"), "w") as f:
            f.write(raw)

        with self.assertRaises(ValueError):
            Config(workspace=self.workspace)

    def test_toml_safe(self):
        """
        Tests the toml safe conversion method.
        """

        value = {
            "path": Path("/test/path"),
            "list": [Path("/test/list"), "value"],
            "tuple": (Path("/test/tuple"), 123),
            "nested": {"path": Path("/test/nested")},
            "string": "value",
        }

        result = Config._toml_safe(value)

        self.assertEqual(
            result,
            {
                "path": "/test/path",
                "list": ["/test/list", "value"],
                "tuple": ["/test/tuple", 123],
                "nested": {"path": "/test/nested"},
                "string": "value",
            },
        )

    def test_get_model_direct(self):
        """
        Tests getting the PyDantic model of an object directly
        """

        result = Config._get_model(TestModel)

        self.assertIs(result, TestModel)

    def test_get_model_optional(self):
        """
        Tests getting the PyDantic model of an optional object
        """

        result = Config._get_model(TestModel | None)

        self.assertIs(result, TestModel)

    def test_get_model_no_model(self):
        """
        Tests getting the PyDantic model of an object with no model
        """

        result = Config._get_model(str)

        self.assertIsNone(result)
