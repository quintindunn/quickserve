"""
Tests simple backups.

Author: Quintin Dunn
Date: 11/18/2026
"""

import tempfile
import unittest
import uuid
import zipfile
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

from QuickServeModuleLibrary.simple_backups import (
    BackupOptions,
    SimpleBackup,
    walk_backup_files,
)


class FakeWorkspace:
    def __init__(self, root: Path):
        self.root = root
        self.temp_path = root / "temp"

    def get_temp_folder(self) -> Path:
        self.temp_path.mkdir()
        return self.temp_path


class FakeInstance:
    def __init__(self, working_dir: Path):
        self.uuid = uuid.uuid4()
        self._working_dir = working_dir

    def working_directory(self) -> Path:
        return self._working_dir


class TestSimpleBackup(unittest.TestCase):
    """
    Tests simple backups
    """

    def setUp(self):
        """
        Sets up the workspace and instance for tests
        """

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

        self.walk_root = self.root / "walk" / "server"
        (self.walk_root / "logs").mkdir(parents=True)
        (self.walk_root / "world" / "region").mkdir(parents=True)
        (self.walk_root / "server.properties").write_text("motd=QuickServe")
        (self.walk_root / "eula.txt").write_text("eula=true")
        (self.walk_root / "logs" / "latest.log").write_text("log")
        (self.walk_root / "world" / "session.lock").write_text("lock")
        (self.walk_root / "world" / "region" / "r.0.0.mca").write_bytes(b"region")

        self.workspace = FakeWorkspace(self.root)
        self.scheduler = SimpleNamespace(submit_recurring_job=lambda **_: None)
        self.base_module = SimpleNamespace(
            scheduler=self.scheduler,
            workspace=self.workspace,
        )
        self.module = SimpleNamespace(module=self.base_module, NAME="TestModule")
        self.instance_dir = self.root / "instance"
        self.instance_dir.mkdir()
        self.instance = FakeInstance(self.instance_dir)

        server = self.instance_dir / "server"
        (server / "logs").mkdir(parents=True)
        (server / "world" / "region").mkdir(parents=True)
        (server / "server.properties").write_text("motd=QuickServe")
        (server / "eula.txt").write_text("eula=true")
        (server / "logs" / "latest.log").write_text("log")
        (server / "world" / "session.lock").write_text("lock")
        (server / "world" / "level.dat").write_bytes(b"world data")
        (server / "world" / "region" / "r.0.0.mca").write_bytes(b"region")

    def test_walk_ignores_files(self):
        """
        Tests that ignored files aren't returned by the walk
        """

        files = set(
            path.relative_to(self.walk_root).as_posix()
            for path in walk_backup_files(
                self.walk_root,
                ["eula.txt", "logs/*", "world/session.lock"],
            )
        )

        self.assertEqual(
            files,
            {"server.properties", "world/region/r.0.0.mca"},
        )

    def make_backup(self, **kwargs) -> SimpleBackup:
        """
        Creates a SimpleBackup object for tests
        """

        return SimpleBackup(
            module=self.module,
            interval=timedelta(hours=1),
            options=BackupOptions(
                root_dir="server",
                backup_dir="backups",
                ignored_paths=["eula.txt", "logs/*", "world/session.lock"],
            ),
            **kwargs,
        )

    def test_backup_writes_zip_with_relative_paths_and_ignores(self):
        """
        Tests that the backup zip contains the right files
        """

        backup = self.make_backup()
        backup.submit_instance(self.instance)

        backup.backup_instance(self.instance)

        archives = list((self.instance_dir / "backups").glob("*.zip"))
        self.assertEqual(len(archives), 1)
        with zipfile.ZipFile(archives[0]) as archive:
            self.assertEqual(
                set(archive.namelist()),
                {
                    "server/server.properties",
                    "server/world/level.dat",
                    "server/world/region/r.0.0.mca",
                },
            )
            self.assertEqual(
                archive.read("server/server.properties"), b"motd=QuickServe"
            )
            self.assertEqual(archive.read("server/world/level.dat"), b"world data")

        self.assertEqual(
            backup.backup_dir_sizes[self.instance.uuid], archives[0].stat().st_size
        )
        self.assertFalse(self.workspace.temp_path.exists())

    def test_backup_calls_pre_and_post_callbacks(self):
        """
        Tests that pre and post backup functions are called
        """

        callback_events = []
        backup = self.make_backup(
            pre_backup_fn=lambda instance: callback_events.append(("pre", instance)),
            post_backup_fn=lambda instance, path: callback_events.append(
                ("post", instance, path.exists())
            ),
        )
        backup.submit_instance(self.instance)

        backup.backup_instance(self.instance)

        self.assertEqual(callback_events[0], ("pre", self.instance))
        self.assertEqual(callback_events[1][0:2], ("post", self.instance))
        self.assertTrue(callback_events[1][2])

    def test_backup_skips_non_running_instance_when_requested(self):
        """
        Tests that an inactive instance is not backed up
        """

        backup = self.make_backup()
        backup.is_alive = lambda instance: False

        backup.backup_instance(self.instance, ignore_is_alive=False)

        self.assertFalse((self.instance_dir / "backups").exists())

    def test_backup_retains_only_configured_number_of_archives(self):
        """
        Tests that old backups are removed when the limit is reached
        """

        backup = self.make_backup(max_stored_backups=2, max_total_backup_size=10**9)
        backup.submit_instance(self.instance)

        for _ in range(3):
            backup.backup_instance(self.instance)

        archives = list((self.instance_dir / "backups").glob("*.zip"))
        self.assertEqual(len(archives), 2)
        self.assertEqual(
            backup.backup_dir_sizes[self.instance.uuid],
            sum(archive.stat().st_size for archive in archives),
        )
