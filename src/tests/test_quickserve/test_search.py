"""
Tests the module/instance searching.

Author: Quintin Dunn
Date: 10/09/2026
"""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from QuickServe.Common.search import Search


class TestSearch(unittest.TestCase):
    """
    Tests module/instance searching.
    """

    def setUp(self):
        self.catalog = MagicMock()
        self.instance_manager = MagicMock()

        self.search: Search = Search(
            catalog=self.catalog,
            instance_manager=self.instance_manager,
        )

    def test_build_module_tfidf_add(self):
        """
        Tests conversion of modules into a document for TfIDF.
        """

        module = SimpleNamespace(
            NAME="TestModule",
            VERSION="1.2.3",
            DESCRIPTION="A test module",
            about=lambda: "<p>This is <strong>about</strong> the module.</p>",
        )

        title, body, minor = self.search._build_module_tfidf_add(module)

        self.assertEqual(
            title,
            "TestModule 1.2.3",
        )
        self.assertEqual(
            body,
            "A test module\n\nThis is about the module.",
        )
        self.assertEqual(minor, "")

    def test_build_instance_tfidf_add(self):
        """
        Tests conversion of instances into a document for TfIDF.
        """

        instance = SimpleNamespace(
            instance_name="My Server",
            module_name="Minecraft",
            uuid="1234",
        )

        title, body, minor = self.search._build_instance_tfidf_add(
            instance,
        )

        self.assertEqual(
            title,
            "My Server Minecraft 1234",
        )
        self.assertEqual(body, "")
        self.assertEqual(minor, "")

    def test_register_module(self):
        """
        Tests registering a module into TfIDF.
        """

        module = SimpleNamespace(
            NAME="TestModule",
            VERSION="1.0",
            DESCRIPTION="A test module",
            about=lambda: "About the module",
        )

        self.search.register_module(module)

        self.assertIn(
            "TestModule",
            self.search.module_registrar,
        )
        self.assertEqual(
            len(self.search.module_tfidf.corpus),
            1,
        )
        self.assertEqual(
            self.search.module_tfidf.corpus[0].identifier,
            "TestModule",
        )

    def test_register_instance(self):
        """
        Tests registering an instance into TfIDF.
        """

        instance = SimpleNamespace(
            instance_name="My Server",
            module_name="Minecraft",
            uuid="1234",
        )

        self.search.register_instance(instance)

        self.assertIn(
            "1234",
            self.search.instance_registrar,
        )
        self.assertEqual(
            len(self.search.instance_tfidf.corpus),
            1,
        )
        self.assertEqual(
            self.search.instance_tfidf.corpus[0].identifier,
            "1234",
        )

    def test_update_modules(self):
        """
        Tests updating the TfIDF's module corpus.
        """

        module1 = SimpleNamespace(
            NAME="Module1",
            VERSION="1.0",
            DESCRIPTION="First module",
            about=lambda: "First",
        )
        module2 = SimpleNamespace(
            NAME="Module2",
            VERSION="1.0",
            DESCRIPTION="Second module",
            about=lambda: "Second",
        )

        self.catalog.items.return_value = [
            ("module1", SimpleNamespace(module=module1)),
            ("module2", SimpleNamespace(module=module2)),
        ]

        self.search.update_modules()

        self.assertEqual(
            self.search.module_registrar,
            {
                "Module1",
                "Module2",
            },
        )
        self.assertEqual(
            len(self.search.module_tfidf.corpus),
            2,
        )

    def test_update_instances(self):
        """
        Tests updating the TfIDF's instance corpus.
        """

        instance1 = SimpleNamespace(
            instance_name="Server 1",
            module_name="Minecraft",
            uuid="1111",
        )
        instance2 = SimpleNamespace(
            instance_name="Server 2",
            module_name="Minecraft",
            uuid="2222",
        )

        self.instance_manager.load_all.return_value = [
            instance1,
            instance2,
        ]

        self.search.update_instances()

        self.assertEqual(
            self.search.instance_registrar,
            {
                "1111",
                "2222",
            },
        )
        self.assertEqual(
            len(self.search.instance_tfidf.corpus),
            2,
        )

    def test_update_all(self):
        """
        Tests updating both of the TfIDF's corpuses.
        """

        self.search.update_modules = MagicMock()
        self.search.update_instances = MagicMock()

        self.search.update_all()

        self.search.update_modules.assert_called_once_with()
        self.search.update_instances.assert_called_once_with()

    def test_search(self):
        """
        Tests searching for modules, and instances.
        """

        module_result = (MagicMock(identifier="module"), 0.9)
        instance_result = (MagicMock(identifier="instance"), 0.8)

        self.search.module_tfidf.query = MagicMock(
            return_value=[module_result],
        )
        self.search.instance_tfidf.query = MagicMock(
            return_value=[instance_result],
        )

        modules, instances = self.search.search(
            "minecraft",
            max_results=10,
        )

        self.assertEqual(
            modules,
            [module_result],
        )
        self.assertEqual(
            instances,
            [instance_result],
        )

        self.search.module_tfidf.query.assert_called_once_with(
            query="minecraft",
            max_results=10,
        )
        self.search.instance_tfidf.query.assert_called_once_with(
            query="minecraft",
            max_results=10,
        )
