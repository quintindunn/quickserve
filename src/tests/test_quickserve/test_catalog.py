"""
Tests for the ModuleCatalog
"""

import unittest

from QuickServe.FileSystem.plugins import ModuleCatalog


class FakeModule:
    """
    Fake module for testing within TestCatalog.
    """

    def __init__(self, instance_name: str, instance_uuid: str, module_name: str):
        self.instance_name: str = instance_name
        self.instance_uuid: str = instance_uuid
        self.module_name = module_name

    def __str__(self):
        return f'<Fake Module \"{self.module_name}\"-"{self.instance_name}" {self.instance_uuid[:16]}>'


class TestCatalog(unittest.TestCase):
    """
    Tests the catalog
    """

    def setUp(self):
        """
        Sets up a starting state for each test.
        """

        self.uuids = [
            "c7011ca1-f685-494e-90f8-c2d544ceb737",
            "a8af1a36-c13d-4603-8f66-ea58be19dc90",
            "8539573c-619e-40d8-80cb-81d9b403bb6b",
            "56e99ed4-bdff-42fe-a967-dcd421dbb08e",
        ]
        modules = {
            "foo": FakeModule(instance_name="foo", instance_uuid=self.uuids[0], module_name="foo"),
            "bar": FakeModule(instance_name="bar", instance_uuid=self.uuids[1], module_name="bar"),
            "foobar": FakeModule(instance_name="foobar", instance_uuid=self.uuids[2], module_name="foobar"),
            "buzz": FakeModule(instance_name="buzz", instance_uuid=self.uuids[3], module_name="buzz"),
        }

        self.catalog = ModuleCatalog(modules)

    def test_get(self):
        """
        Tests getting a key from the catalog
        """

        catalog_1 = self.catalog.get("foo")
        self.assertEqual(catalog_1.instance_uuid, self.uuids[0])

        catalog_2 = self.catalog.get("bar")
        self.assertEqual(catalog_2.instance_uuid, self.uuids[1])

        catalog_3 = self.catalog.get("foobar")
        self.assertEqual(catalog_3.instance_uuid, self.uuids[2])

        catalog_4 = self.catalog.get("buzz")
        self.assertEqual(catalog_4.instance_uuid, self.uuids[3])

        catalog_5 = self.catalog.get("non-existent")
        self.assertIsNone(catalog_5)

    def test_require(self):
        """
        Tests getting a key from the catalog, and non-existent keys throws errors.
        """

        catalog_1 = self.catalog.require("foo")
        self.assertEqual(catalog_1.instance_uuid, self.uuids[0])

        catalog_2 = self.catalog.require("bar")
        self.assertEqual(catalog_2.instance_uuid, self.uuids[1])

        catalog_3 = self.catalog.require("foobar")
        self.assertEqual(catalog_3.instance_uuid, self.uuids[2])

        catalog_4 = self.catalog.require("buzz")
        self.assertEqual(catalog_4.instance_uuid, self.uuids[3])

        with self.assertRaises(KeyError):
            self.catalog.require("non-existent")

    def test_contains(self):
        """
        Tests the __contains__ overload in ModuleCatalog.
        """

        self.assertTrue("foo" in self.catalog)
        self.assertTrue("bar" in self.catalog)
        self.assertTrue("foobar" in self.catalog)
        self.assertTrue("buzz" in self.catalog)

        self.assertFalse("True" in self.catalog)
        self.assertFalse("" in self.catalog)
        self.assertFalse("non-existent" in self.catalog)
        self.assertFalse("a" * 255 in self.catalog)
        with self.assertRaises(KeyError):
            self.catalog.require("non-existent")

    def test_items(self):
        """
        Tests that Catalog.items() gets all the items in the catalog.
        """

        items = list(self.catalog.items())
        self.assertEqual(len(items), len(self.uuids))

    def test_modules(self):
        """
        Tests that Catalog.modules() gets all the items in a copy.
        """

        modules = self.catalog.modules
        self.assertEqual(modules, dict(self.catalog.items()))

        modules.pop(next(iter(modules.keys())))

        self.assertNotEqual(modules, dict(self.catalog.items()))
