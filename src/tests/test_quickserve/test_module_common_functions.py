"""
Tests module common registry

Author: Quintin Dunn
Date: 10/08/2026
"""

import unittest

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, Mock
from datetime import datetime

from flask import Flask
from markupsafe import Markup

from QuickServe.Web.module_common.exceptions import ResourceDoesntExistException
from QuickServe.Web.module_common.resources import get_resource
from QuickServe.Web.module_common.factories.action import action_builder
from QuickServe.Web.module_common.factories.link import link_builder
from QuickServe.Web.module_common.factories.resource import resource_builder
from QuickServe.Web.module_common.factories.simple_controller import (
    simple_controller_builder,
)
from QuickServe.Web.module_common.factories.simple_fs import (
    simple_filesystem_builder,
    is_child,
)
from QuickServe.Web.module_common.factories.simple_fs import _redirect as redirect  # noqa

from flask import request


class TestModuleCommonFunctions(unittest.TestCase):
    """
    Tests the module common functions
    """

    def test_get_resource_exists_read(self):
        """
        Tests getting resources in "r" mode.
        """

        asset = get_resource("simple_controller.html", mode="r")
        self.assertIsInstance(asset, str)

    def test_get_resource_exists_read_bytes(self):
        """
        Tests getting resources in "rb" mode.
        """

        asset = get_resource("simple_controller.html", mode="rb")
        self.assertIsInstance(asset, bytes)

    def test_get_resource_not_exist(self):
        """
        Tests getting a non-existent resource.
        """

        with self.assertRaises(ResourceDoesntExistException):
            get_resource("non-existent.quickserve")

    def test_action(self):
        """
        Tests the action function returns the correct url.
        """

        with patch(
            "QuickServe.Web.module_common.factories.action.url_for"
        ) as mock_url_for:
            mock_url_for.return_value = "/module/mymodule/action/start"

            action = action_builder("mymodule")
            result = action("start")

            mock_url_for.assert_called_once_with(
                "modules.action",
                module_name="mymodule",
                method="start",
            )
            self.assertEqual(result, "/module/mymodule/action/start")

    def test_module_link(self):
        """
        Tests the link function when within a module url returns the correct url.
        """

        with patch(
            "QuickServe.Web.module_common.factories.link.url_for"
        ) as mock_url_for:
            mock_url_for.return_value = "/module/mymodule/about"

            link = link_builder("mymodule")
            result = link("about")

            mock_url_for.assert_called_once_with(
                "modules.module_page",
                module_name="mymodule",
                page="about",
            )
            self.assertEqual(result, "/module/mymodule/about")

    def test_instance_link(self):
        """
        Tests the link when within an instance url returns the correct url.
        """

        with patch(
            "QuickServe.Web.module_common.factories.link.url_for"
        ) as mock_url_for:
            mock_url_for.return_value = "/instance/123/about"

            link = link_builder("mymodule", "123")
            result = link("about")

            mock_url_for.assert_called_once_with(
                "modules.instances.module_instance",
                uuid="123",
                page="about",
            )
            self.assertEqual(result, "/instance/123/about")

    def test_resource(self):
        """
        Tests the that the resource function returns the correct url for a given resource.
        """

        with patch(
            "QuickServe.Web.module_common.factories.resource.url_for"
        ) as mock_url_for:
            mock_url_for.return_value = "/module/mymodule/foo.txt"

            resource = resource_builder("mymodule")
            result = resource("foo.txt")

            mock_url_for.assert_called_once_with(
                "modules.resource",
                module_name="mymodule",
                filename="foo.txt",
            )
            self.assertEqual(result, "/module/mymodule/foo.txt")

    def test_simple_controller(self):
        """
        Tests that the simple controller renders its template with the correct context and returns the rendered HTML as Markup.
        """

        app = Flask(__name__)

        with patch(
            "QuickServe.Web.module_common.factories.simple_controller.get_resource",
            return_value="<div>mymodule</div>",
        ) as mock_get_resource:
            websocket_server = Mock(host="192.168.1.98", port=5001)

            with (
                app.app_context(),
                app.test_request_context(),
            ):
                request.instance = Mock()

                with patch.object(app.jinja_env, "from_string") as mock_from_string:
                    mock_from_string.return_value.render.return_value = (
                        "<div>rendered</div>"
                    )

                    controller = simple_controller_builder("mymodule", websocket_server)
                    result = controller()

                    mock_get_resource.assert_called_once_with(
                        "simple_controller.html", mode="r"
                    )
                    mock_from_string.assert_called_once_with("<div>mymodule</div>")
                    mock_from_string.return_value.render.assert_called_once_with(
                        context={
                            "module_name": "mymodule",
                            "websocket_host": "192.168.1.98",
                            "websocket_port": 5001,
                        }
                    )
                    self.assertIsInstance(result, Markup)
                    self.assertEqual(str(result), "<div>rendered</div>")

    def test_simple_controller_0_0_0_0_host(self):
        """
        Tests the simple controller function returns a non 0.0.0.0 host when host is 0.0.0.0.
        """

        app = Flask(__name__)

        with (
            patch(
                "QuickServe.Web.module_common.factories.simple_controller.get_resource",
                return_value="<div>mymodule</div>",
            ),
            patch(
                "QuickServe.Web.module_common.factories.simple_controller.local_ip",
                "192.168.1.50",
            ),
        ):
            websocket_server = Mock(host="0.0.0.0", port=5001)

            with (
                app.app_context(),
                app.test_request_context(),
            ):
                request.instance = Mock()

                with patch.object(app.jinja_env, "from_string") as mock_from_string:
                    mock_from_string.return_value.render.return_value = (
                        "<div>rendered</div>"
                    )

                    controller = simple_controller_builder("mymodule", websocket_server)
                    controller()

                    mock_from_string.return_value.render.assert_called_once_with(
                        context={
                            "module_name": "mymodule",
                            "websocket_host": "192.168.1.50",
                            "websocket_port": 5001,
                        }
                    )


class TestSimpleFilesystemBuilder(unittest.TestCase):
    """
    Tests for the simple filesystem.
    """

    def setUp(self):
        self.app = Flask(__name__)
        self.temp_dir = TemporaryDirectory()
        self.working_dir = Path(self.temp_dir.name)

        self.instance = Mock()
        self.instance.working_directory.return_value = self.working_dir

    def tearDown(self):
        self.temp_dir.cleanup()

    def _build_filesystem(self):
        """
        Build the filesystem callable with mocked templates.
        """

        with patch(
            "QuickServe.Web.module_common.factories.simple_fs.get_resource",
            side_effect=[
                "<div>folder</div>",
                "<div>file</div>",
            ],
        ) as mock_get_resource:
            filesystem = simple_filesystem_builder("mymodule")

        mock_get_resource.assert_any_call(
            "simple_filesystem_folder_viewer.html", mode="r"
        )
        mock_get_resource.assert_any_call(
            "simple_filesystem_file_viewer.html", mode="r"
        )
        self.assertEqual(mock_get_resource.call_count, 2)

        return filesystem

    def test_simple_fs_folder_listing(self):
        """
        Test that the filesystem lists files and folders in the root directory.
        """

        (self.working_dir / "folder").mkdir()
        (self.working_dir / "empty").mkdir()
        (self.working_dir / "file.txt").write_text("hello")

        filesystem = self._build_filesystem()

        with (
            self.app.app_context(),
            self.app.test_request_context("/?directory="),
        ):
            request.instance = self.instance

            with patch.object(self.app.jinja_env, "from_string") as mock_from_string:
                mock_from_string.return_value.render.return_value = (
                    "<div>rendered</div>"
                )

                result = filesystem()

                self.assertIsInstance(result, Markup)
                mock_from_string.assert_called_once_with("<div>folder</div>")

                context = mock_from_string.return_value.render.call_args.kwargs[
                    "context"
                ]

                self.assertEqual(context["module_name"], "mymodule")
                self.assertEqual(context["instance"], self.instance)
                self.assertEqual(context["root_directory"], "./")
                self.assertEqual(context["parent_folder"], Path("."))

                files = {item["filename"]: item for item in context["files"]}

                self.assertEqual(set(files), {"folder", "empty", "file.txt"})
                self.assertTrue(files["folder"]["isDir"])
                self.assertFalse(files["folder"]["isFile"])
                self.assertTrue(files["empty"]["isEmptyDir"])
                self.assertTrue(files["file.txt"]["isFile"])
                self.assertFalse(files["file.txt"]["isDir"])
                self.assertEqual(files["file.txt"]["size"], "0.0kb")
                self.assertEqual(files["file.txt"]["cwd"], "/")

                expected_date = datetime.fromtimestamp(
                    (self.working_dir / "file.txt").stat().st_mtime
                ).strftime("%m/%d/%Y %I:%M:%S%p")

                self.assertEqual(files["file.txt"]["modified"], expected_date)

    def test_simple_fs_nested_folder_listing(self):
        """
        Test that the filesystem lists the contents of a nested directory.
        """

        nested_dir = self.working_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "file.txt").write_text("hello")

        filesystem = self._build_filesystem()

        with (
            self.app.app_context(),
            self.app.test_request_context("/?directory=nested"),
        ):
            request.instance = self.instance

            with patch.object(self.app.jinja_env, "from_string") as mock_from_string:
                mock_from_string.return_value.render.return_value = (
                    "<div>rendered</div>"
                )

                filesystem()

                context = mock_from_string.return_value.render.call_args.kwargs[
                    "context"
                ]

                self.assertEqual(context["module_name"], "mymodule")
                self.assertEqual(context["root_directory"], "./nested")
                self.assertEqual(context["parent_folder"], Path("."))
                self.assertEqual(context["files"][0]["filename"], "file.txt")
                self.assertEqual(context["files"][0]["cwd"], "nested/")

    def test_simple_fs_folder_traversal_returns_empty_listing(self):
        """
        Test that directory traversal does not list files outside the root of the SimpleFS.
        """

        filesystem = self._build_filesystem()

        with (
            self.app.app_context(),
            self.app.test_request_context("/?directory=../"),
        ):
            request.instance = self.instance

            with patch.object(self.app.jinja_env, "from_string") as mock_from_string:
                mock_from_string.return_value.render.return_value = (
                    "<div>rendered</div>"
                )

                filesystem()

                context = mock_from_string.return_value.render.call_args.kwargs[
                    "context"
                ]

                self.assertEqual(context["files"], [])

    def test_simple_fs_render_file_traversal_redirects(self):
        """
        Test that trying to open files outside the root are redirected.
        """

        outside_file = self.working_dir.parent / "outside.txt"
        outside_file.write_text("secret")

        try:
            filesystem = self._build_filesystem()

            with (
                self.app.app_context(),
                self.app.test_request_context("/?file=../outside.txt"),
            ):
                request.instance = self.instance

                result = filesystem()

                self.assertIsInstance(result, Markup)
                self.assertIn("window.location = `/`;", str(result))
        finally:
            outside_file.unlink(missing_ok=True)

    def test_simple_fs_missing_instance_raises(self):
        """
        Test that it raises an error when trying to view a file outside the FS
        """

        filesystem = self._build_filesystem()

        with (
            self.app.app_context(),
            self.app.test_request_context("/"),
        ):
            with self.assertRaises(AssertionError):
                filesystem()

    def test_simple_fs_is_child(self):
        """
        Test that is_child correctly identifies paths within the root.
        """

        root = self.working_dir
        child = root / "subdir" / "file.txt"

        self.assertTrue(is_child(root, child))
        self.assertTrue(is_child(root, root))
        self.assertFalse(is_child(root, root.parent))
        self.assertFalse(is_child(root, root / ".." / "outside.txt"))

    def test_simple_fs_redirect(self):
        """
        Test that redirect properly generates a redirect.
        """

        result = redirect("/module/mymodule")

        self.assertIsInstance(result, Markup)
        self.assertIn(
            "window.location = `/module/mymodule`;",
            str(result),
        )
