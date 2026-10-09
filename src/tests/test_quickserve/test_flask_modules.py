"""
Tests the modules blueprint for the flask app.

Author: Quintin Dunn
Date: 10/09/2026
"""

import base64
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock

from flask import Flask

from QuickServe.Web.modules import modules, _get_path, _get_working_dir  # noqa


class TestModuleBlueprint(TestCase):
    """
    Tests for the module blueprint.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.working_dir = self.root / "instance"
        self.working_dir.mkdir()

        self.instance = MagicMock()
        self.instance.uuid = "test-uuid"
        self.instance.module_name = "mymodule"
        self.instance.instance_name = "Test Instance"
        self.instance.working_directory.return_value = self.working_dir
        self.instance.base_module.module.FS_ROOT = ""

        self.instance_manager = MagicMock()
        self.instance_manager.from_uuid.return_value = self.instance

        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.register_blueprint(modules)

        self.app.extensions["quickserve.instance_manager"] = self.instance_manager

        self.client = self.app.test_client()
        self.url = "/module/instancestatic/test-uuid/"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_working_dir(self):
        """
        Test resolving the instance working directory.
        """

        self.assertEqual(
            _get_working_dir(self.instance),
            self.working_dir.resolve(),
        )

    def test_get_path(self):
        """
        Test resolving paths within the instance directory.
        """

        file = self.working_dir / "test.txt"
        file.touch()

        self.assertEqual(
            _get_path(self.instance, "test.txt"),
            file.resolve(),
        )

    def test_get_path_missing(self):
        """
        Test resolving a nonexistent file.
        """

        self.assertIsNone(_get_path(self.instance, "missing.txt"))

    def test_get_path_traversal(self):
        """
        Test rejecting paths outside the instance directory.
        """

        outside = self.root / "outside.txt"
        outside.touch()

        self.assertIsNone(_get_path(self.instance, "../outside.txt"))

    def test_create_file(self):
        """
        Test creating a file.
        """

        response = self.client.post(
            self.url + "createfile/",
            json={"cwd": "/", "filename": "test.txt"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue((self.working_dir / "test.txt").is_file())

    def test_create_file_already_exists(self):
        """
        Test rejecting an existing filename.
        """

        (self.working_dir / "test.txt").touch()

        response = self.client.post(
            self.url + "createfile/",
            json={"cwd": "/", "filename": "test.txt"},
        )

        self.assertEqual(response.status_code, 400)

    def test_create_file_invalid_name(self):
        """
        Test rejecting filenames containing path separators.
        """

        response = self.client.post(
            self.url + "createfile/",
            json={"cwd": "/", "filename": "../test.txt"},
        )

        self.assertEqual(response.status_code, 400)

    def test_create_file_missing_filename(self):
        """
        Test rejecting a request without a filename.
        """

        response = self.client.post(
            self.url + "createfile/",
            json={"cwd": "/"},
        )

        self.assertEqual(response.status_code, 400)

    def test_create_folder(self):
        """
        Test creating a folder.
        """

        response = self.client.post(
            self.url + "createfolder/",
            json={"cwd": "/", "foldername": "test"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue((self.working_dir / "test").is_dir())

    def test_create_folder_already_exists(self):
        """
        Test rejecting an existing folder.
        """

        (self.working_dir / "test").mkdir()

        response = self.client.post(
            self.url + "createfolder/",
            json={"cwd": "/", "foldername": "test"},
        )

        self.assertEqual(response.status_code, 400)

    def test_save_file(self):
        """
        Test saving file contents.
        """

        file = self.working_dir / "test.txt"
        file.write_bytes(b"old content")

        content = base64.b64encode(b"new content").decode()

        response = self.client.post(
            self.url + "savefile/",
            json={"filepath": "test.txt", "content": content},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(file.read_bytes(), b"new content")

    def test_save_file_missing(self):
        """
        Test rejecting a request without a filepath.
        """

        response = self.client.post(
            self.url + "savefile/",
            json={"content": "dGVzdA=="},
        )

        self.assertEqual(response.status_code, 400)

    def test_save_file_traversal(self):
        """
        Test preventing writes outside the instance directory.
        """

        outside = self.root / "outside.txt"
        outside.write_bytes(b"original")

        content = base64.b64encode(b"modified").decode()

        response = self.client.post(
            self.url + "savefile/",
            json={"filepath": "../outside.txt", "content": content},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(outside.read_bytes(), b"original")

    def test_download_file(self):
        """
        Test downloading a file.
        """

        file = self.working_dir / "test.txt"
        file.write_bytes(b"download content")

        response = self.client.post(
            self.url + "downloadfile/",
            json={"filepath": "test.txt"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"download content")

    def test_download_missing_file(self):
        """
        Test rejecting a nonexistent file download.
        """

        response = self.client.post(
            self.url + "downloadfile/",
            json={"filepath": "missing.txt"},
        )

        self.assertEqual(response.status_code, 400)

    def test_delete_file(self):
        """
        Test deleting a file.
        """

        file = self.working_dir / "test.txt"
        file.touch()

        response = self.client.post(
            self.url + "deletepath/",
            json={"filepath": "test.txt"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(file.exists())

    def test_delete_empty_folder(self):
        """
        Test deleting an empty folder.
        """

        folder = self.working_dir / "test"
        folder.mkdir()

        response = self.client.post(
            self.url + "deletepath/",
            json={"filepath": "test"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(folder.exists())

    def test_delete_nonempty_folder(self):
        """
        Test rejecting deletion of a nonempty folder.
        """

        folder = self.working_dir / "test"
        folder.mkdir()
        (folder / "file.txt").touch()

        response = self.client.post(
            self.url + "deletepath/",
            json={"filepath": "test"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(folder.exists())

    def test_delete_working_directory(self):
        """
        Test preventing deletion of the instance root.
        """

        response = self.client.post(
            self.url + "deletepath/",
            json={"filepath": "/"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(self.working_dir.exists())

    def test_rename_file(self):
        """
        Test renaming a file.
        """

        source = self.working_dir / "old.txt"
        destination = self.working_dir / "new.txt"
        source.write_text("content")

        response = self.client.post(
            self.url + "renamefile/",
            json={"cwd": "/", "src": "old.txt", "dst": "new.txt"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(source.exists())
        self.assertEqual(destination.read_text(), "content")

    def test_rename_file_destination_exists(self):
        """
        Test rejecting a rename to an existing destination.
        """

        source = self.working_dir / "old.txt"
        destination = self.working_dir / "new.txt"
        source.touch()
        destination.touch()

        response = self.client.post(
            self.url + "renamefile/",
            json={"cwd": "/", "src": "old.txt", "dst": "new.txt"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(source.exists())

    def test_rename_file_invalid_destination(self):
        """
        Test rejecting a destination containing a path separator.
        """

        (self.working_dir / "old.txt").touch()

        response = self.client.post(
            self.url + "renamefile/",
            json={"cwd": "/", "src": "old.txt", "dst": "../new.txt"},
        )

        self.assertEqual(response.status_code, 400)

    def test_rename_file_missing_source(self):
        """
        Test rejecting a rename when the source doesn't exist.
        """

        response = self.client.post(
            self.url + "renamefile/",
            json={"cwd": "/", "src": "missing.txt", "dst": "new.txt"},
        )

        self.assertEqual(response.status_code, 400)
