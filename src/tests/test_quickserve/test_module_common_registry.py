"""
Tests module common registry

Author: Quintin Dunn
Date: 10/08/2026
"""

import unittest
from unittest.mock import MagicMock

from QuickServe.Web.module_common.registry import Registry
from QuickServe.Web.module_common.factories.action import action_builder
from QuickServe.Web.module_common.factories.link import link_builder
from QuickServe.Web.module_common.factories.resource import resource_builder


class TestModuleCommonFunctionRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = Registry(MagicMock())

    def test_default_registrations(self):
        """Test that the default factories are registered correctly."""

        self.assertEqual(
            set(self.registry.registered),
            {
                "simple_controller",
                "simple_filesystem",
                "action",
                "link",
                "resource",
            },
        )

        self.assertIs(self.registry.registered["action"], action_builder)
        self.assertIs(self.registry.registered["link"], link_builder)
        self.assertIs(self.registry.registered["resource"], resource_builder)

    def test_register(self):
        """Test that a factory can be registered."""

        factory = MagicMock()

        self.registry.register("foo", factory)

        self.assertIs(self.registry.registered["foo"], factory)
