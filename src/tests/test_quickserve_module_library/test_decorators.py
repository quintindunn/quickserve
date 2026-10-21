"""
Tests the QuickServeModuleLibrary decorators.

Author: Quintin Dunn
Date: 10/21/2026
"""

import unittest
from unittest.mock import Mock, patch

from QuickServeModuleLibrary.decorators import (
    ActionDefinition,
    PageDefinition,
    RegisteredCallable,
    action,
    page,
)


class TestRegisteredCallable(unittest.TestCase):
    """
    Tests the execution of registered callables.
    """

    def setUp(self):
        """
        Creates a mock module and function for callable tests.
        """
        self.module = object()
        self.func = Mock(return_value="result")

    def test_calls_function(self):
        """
        Passes the module and supplied arguments to a regular callable.
        """
        registered = RegisteredCallable(self.func, "home", self.module)

        result = registered(1, key="value")

        self.assertEqual(result, "result")
        self.func.assert_called_once_with(self.module, 1, key="value")

    def test_unbound_module_raises_error(self):
        """
        Raises RuntimeError when the callable has no bound module.
        """
        registered = RegisteredCallable(self.func, "home", None)

        with self.assertRaisesRegex(
            RuntimeError, "Callable 'home' is not bound to a module"
        ):
            registered()

        self.func.assert_not_called()

    def test_instance_specific_call(self):
        """
        Passes the current request instance to an instance-specific callable.
        """
        instance = object()
        request_mock = Mock()
        request_mock.instance = instance

        registered = RegisteredCallable(
            self.func,
            "details",
            self.module,
            instance_specific=True,
        )

        with patch(
            "QuickServeModuleLibrary.decorators._request",
            new=request_mock,
        ):
            result = registered(1, key="value")

        self.assertEqual(result, "result")
        self.func.assert_called_once_with(self.module, instance, 1, key="value")

    @patch("QuickServeModuleLibrary.decorators._request", new=Mock(spec=[]))
    def test_instance_specific_call_without_instance(self):
        """
        Returns a 404 response without calling the function if no instance exists.
        """
        registered = RegisteredCallable(
            self.func,
            "details",
            self.module,
            instance_specific=True,
        )

        result = registered()

        self.assertIn("404 Not Found!", result)
        self.assertIn("Page not found!", result)
        self.func.assert_not_called()


class TestDefinition(unittest.TestCase):
    """
    Tests descriptor binding and registration of decorated methods.
    """

    def test_class_access(self):
        """
        Returns the page descriptor when accessing a decorated method on its class.
        """

        class Module:
            @page
            def home(self):
                return "home"

        self.assertIsInstance(Module.home, PageDefinition)

    def test_instance_access(self):
        """
        Binds a decorated method to its module instance when accessed on that instance.
        """

        class Module:
            @page
            def home(self, value):
                return value

        module = Module()

        self.assertEqual(module.home("result"), "result")

    def test_instance_specific_access(self):
        """
        Passes the request's instance to a page accessed through its module.
        """
        instance = object()
        request_mock = Mock()
        request_mock.instance = instance

        class Module:
            @page(instance_specific=True)
            def details(self, current_instance):
                return current_instance

        with patch(
            "QuickServeModuleLibrary.decorators._request",
            new=request_mock,
        ):
            result = Module().details()

        self.assertIs(result, instance)

    @patch("QuickServeModuleLibrary.decorators._request", new=Mock(spec=[]))
    def test_instance_specific_access_without_instance(self):
        """
        Returns a 404 response when an instance-specific page has no request instance.
        """

        class Module:
            @page(instance_specific=True)
            def details(self, _):
                return "details"

        result = Module().details()

        self.assertIn("404 Not Found!", result)
        self.assertIn("Page not found!", result)

    def test_page_registration(self):
        """
        Preserves initialization arguments and registers decorated pages.
        """

        class Module:
            def __init__(self, value):
                self.value = value

            @page
            def home(self):
                return "home"

        module = Module(42)

        self.assertEqual(module.value, 42)
        self.assertIn("home", module.QS_INTERNAL_REGISTERED_PAGES)  # noqa
        self.assertIsInstance(
            module.QS_INTERNAL_REGISTERED_PAGES["home"],  # noqa
            RegisteredCallable,
        )
        self.assertEqual(
            module.QS_INTERNAL_REGISTERED_PAGES["home"](),  # noqa
            "home",
        )

    def test_action_registration(self):
        """
        Registers decorated actions and allows them to be executed.
        """

        class Module:
            @action
            def refresh(self):
                return "refreshed"

        module = Module()

        self.assertIn("refresh", module.QS_INTERNAL_REGISTERED_ACTIONS)  # noqa
        self.assertEqual(
            module.QS_INTERNAL_REGISTERED_ACTIONS["refresh"](),  # noqa
            "refreshed",
        )

    def test_custom_names(self):
        """
        Uses custom page and action names instead of their function names.
        """

        class Module:
            @page(page_name="landing")
            def home(self):
                return "home"

            @action(action_name="reload")
            def refresh(self):
                return "refresh"

        module = Module()

        self.assertIn("landing", module.QS_INTERNAL_REGISTERED_PAGES)  # noqa
        self.assertNotIn("home", module.QS_INTERNAL_REGISTERED_PAGES)  # noqa
        self.assertIn("reload", module.QS_INTERNAL_REGISTERED_ACTIONS)  # noqa
        self.assertNotIn("refresh", module.QS_INTERNAL_REGISTERED_ACTIONS)  # noqa


class TestDecorators(unittest.TestCase):
    """
    Tests the public page and action decorator interfaces.
    """

    def test_page_defaults(self):
        """
        Allows a page to be declared using @page without arguments.
        """

        @page
        def home(_):
            return "home"

        self.assertIsInstance(home, PageDefinition)
        self.assertEqual(home.name, "home")
        self.assertFalse(home.instance_specific)

    def test_page_options(self):
        """
        Supports a custom page name and instance-specific page registration.
        """

        @page(page_name="landing", instance_specific=True)
        def home(self, instance):
            return instance

        self.assertIsInstance(home, PageDefinition)
        self.assertEqual(home.name, "landing")
        self.assertTrue(home.instance_specific)

    def test_action_defaults(self):
        """
        Allows an action to be declared using @action without arguments.
        """

        @action
        def refresh(_):
            return "refresh"

        self.assertIsInstance(refresh, ActionDefinition)
        self.assertEqual(refresh.name, "refresh")

    def test_action_options(self):
        """
        Supports a custom registered name for an action.
        """

        @action(action_name="reload")
        def refresh(_):
            return "refresh"

        self.assertIsInstance(refresh, ActionDefinition)
        self.assertEqual(refresh.name, "reload")
