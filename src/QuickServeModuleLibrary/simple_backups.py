"""
A tool for creating server backups.

Author: Quintin Dunn
Date: 11/18/2026
"""

import dataclasses
import logging
import os
import shutil
import zipfile
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Callable
from uuid import UUID
from datetime import datetime

from QuickServeModuleLibrary.simple_controller import SimpleControllerProcessManager

if TYPE_CHECKING:
    from QuickServe.contracts import Module
    from QuickServe.Driver.instance.base_instance import BaseInstance
    from QuickServe.Scheduler.scheduler import RecurringJob

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class BackupOptions:
    root_dir: str | Path
    backup_dir: str | Path
    ignored_paths: list[str | Path]


# e.g.
# minecraft_backup_options: BackupOptions = BackupOptions(
#     root_dir="server",
#     ignored_paths=[
#         "eula.txt",
#         "logs/*",
#         "world/session.lock"
#     ]
# )


def walk_backup_files(
    root_dir: Path, ignored_paths: list[str | Path]
) -> Iterator[Path]:
    """
    Walks the instance working directory starting from the root_dir specified in BackupOptions, following the defined rules.

    :param root_dir: The starting directory for the walk
    :param ignored_paths: The paths to ignore.
    """

    root_dir = Path(root_dir)
    patterns = [Path(path).as_posix().rstrip("/") for path in ignored_paths]

    for current_dir, directory_names, file_names in os.walk(root_dir, topdown=True):
        current_path = Path(current_dir)
        relative_dir = current_path.relative_to(root_dir)

        included_directories = []
        for name in directory_names:
            relative_directory = relative_dir / name
            if any(relative_directory.match(pattern) for pattern in patterns):
                logger.debug(
                    "Skipping backup directory %s because it matches an ignore pattern.",
                    relative_directory,
                )
            else:
                included_directories.append(name)
        directory_names[:] = included_directories

        for file_name in file_names:
            relative_file = relative_dir / file_name
            if any(relative_file.match(pattern) for pattern in patterns):
                logger.debug(
                    "Skipping backup file %s because it matches an ignore pattern.",
                    relative_file,
                )
            else:
                yield current_path / file_name


class SimpleBackup:
    """
    Makes creating server backups easy!
    """

    def __init__(
        self,
        module: "Module",
        interval: timedelta,
        options: "BackupOptions",
        pre_backup_fn: "Callable[[BaseInstance], None] | None" = None,
        post_backup_fn: "Callable[[BaseInstance, Path], None] | None" = None,
        max_stored_backups: int = -1,
        max_total_backup_size: int = -1,
    ):
        self._base_module = module.module
        self._module = module
        self._interval = interval
        self._scheduler = self._base_module.scheduler

        self._pre_backup_fn = pre_backup_fn
        self._post_backup_fn = post_backup_fn

        self._max_stored_backups = max_stored_backups
        self._max_total_backup_size = max_total_backup_size

        self.recurring_jobs: dict[UUID, RecurringJob] = dict()

        self.instances: dict[UUID, BaseInstance] = dict()

        self.backup_dir_sizes: dict[UUID, int] = dict()

        self._options = options

    def backup_dir(self):
        return self._options.backup_dir

    def backup_instance(self, instance: "BaseInstance", ignore_is_alive=True) -> None:
        """
        Performs a backup on an instance.
        :param instance: The instance to backup.
        :param ignore_is_alive: If true the instance will be backed up regardless of if the instance is running or not.
        :return: None
        """

        if self._pre_backup_fn:
            self._pre_backup_fn(instance)

        if not ignore_is_alive and not self.is_alive(instance=instance):
            logger.debug(
                "Not backing up instance %s because it's not running!", instance.uuid
            )
            return

        logger.info(f"Backing up instance {instance.uuid}.")

        instance_working_dir = instance.working_directory()
        root_dir = instance_working_dir / self._options.root_dir
        backup_dir = (instance_working_dir / self._options.backup_dir).resolve()
        if not backup_dir.is_relative_to(instance_working_dir.resolve()):
            logger.error("Cannot save backups outside of instance working dir!")
            return

        workspace = self._base_module.workspace
        zip_file_name = (
            "Backup-" + datetime.now().isoformat().replace(":", "-") + ".zip"
        )

        tmp_folder = None
        try:
            tmp_folder = workspace.get_temp_folder()
            tmp_zip_path = tmp_folder / zip_file_name

            with zipfile.ZipFile(
                tmp_zip_path, mode="w", compression=zipfile.ZIP_DEFLATED
            ) as backup_zip:
                for file_path in walk_backup_files(
                    root_dir, self._options.ignored_paths
                ):
                    relative_path = file_path.relative_to(instance_working_dir)
                    logger.debug("Adding file to backup archive: %s", relative_path)
                    backup_zip.write(file_path, arcname=relative_path.as_posix())

            resolved_instance_dir = instance_working_dir.resolve()
            final_zip_location = (
                instance_working_dir / self._options.backup_dir / zip_file_name
            )
            if not final_zip_location.resolve().is_relative_to(resolved_instance_dir):
                logger.error("Cannot save zip outside of instance working dir!")
            else:
                os.makedirs(final_zip_location.parent, exist_ok=True)
                shutil.move(tmp_zip_path, final_zip_location)
                self.backup_dir_sizes[
                    instance.uuid
                ] += final_zip_location.stat().st_size
        finally:
            if tmp_folder:
                shutil.rmtree(tmp_folder)

        self.remove_old_backups(instance=instance)

        if self._post_backup_fn:
            self._post_backup_fn(instance, final_zip_location)

    def single_submit_instance(
        self, instance: "BaseInstance", ignore_is_alive: bool = True
    ):
        if instance.uuid not in self.backup_dir_sizes:
            self.load_saved_backups(instance=instance)
        self.backup_instance(instance=instance, ignore_is_alive=ignore_is_alive)

    def remove_old_backups(self, instance: "BaseInstance"):
        """
        Removes old backups to comply with the BackupOptions passed into SimpleBackup
        :param instance: The instance to remove old backups from
        :return: None
        """
        instance_working_dir = instance.working_directory().resolve()
        backups_dir = (
            instance.working_directory() / self._options.backup_dir
        ).resolve()

        if not backups_dir.is_relative_to(instance_working_dir):
            logger.error(
                "Backup directory cannot be outside of instance working directory, aborting cleanup!"
            )
            return

        if self._max_stored_backups <= 0 or self._max_total_backup_size <= 0:
            return

        if not backups_dir.is_dir():
            return

        files = sorted(
            (file for file in backups_dir.iterdir() if file.is_file()),
            key=lambda file: file.stat().st_mtime,
            reverse=True,
        )

        while files and (
            len(files) > self._max_stored_backups
            or self.backup_dir_sizes[instance.uuid] > self._max_total_backup_size
        ):
            oldest = files.pop()
            size = oldest.stat().st_size

            os.remove(oldest)
            self.backup_dir_sizes[instance.uuid] -= size

    def _initialize_recurring_job(self, instance: "BaseInstance") -> None:
        """
        Initializes a new recurring job with the scheduler.
        :param instance: The instance to schedule a recurring job for.
        :return: None
        """
        self._scheduler.submit_recurring_job(
            interval=self._interval,
            func=self.backup_instance,
            kwargs={"instance": instance, "ignore_is_alive": False},
        )
        return None

    def is_alive(self, instance: "BaseInstance") -> bool:
        """
        Checks if an instance is currently running.
        :param instance: The instance to check.
        :return: None
        """

        if not hasattr(self._module, "QS_INTERNAL_SIMPLE_PROCESS_MANAGER"):
            logger.warning(
                "Not using SimpleProcessManager, and a custom is_alive is not function set for module %s",
                self._module.NAME,
            )
            return False

        simple_process_manager: "SimpleControllerProcessManager" = (
            self._module.QS_INTERNAL_SIMPLE_PROCESS_MANAGER
        )  # noqa

        process = simple_process_manager.get_process(instance=instance)

        if process is None:
            return False

        return process.is_alive()

    def clear_instances(self) -> None:
        """
        Clears all instances to backup, cancels the job.
        :return: None
        """

        logger.info("Clearing all instances to backup for module %s", self._module.NAME)
        for uuid, instance in self.instances.items():
            if uuid in self.recurring_jobs:
                self.recurring_jobs[uuid].cancelled = True

    def remove_instance(self, instance: "BaseInstance") -> None:
        """
        Removes an instance from the backup queue.
        :param instance:
        :return: None
        """

        if instance.uuid not in self.instances:
            return None

        self.instances.pop(instance.uuid)

        if instance.uuid in self.recurring_jobs:
            self.recurring_jobs[instance.uuid].cancelled = True
            self.recurring_jobs.pop(instance.uuid)

        return None

    def submit_instance(self, instance: "BaseInstance") -> None:
        """
        Submits a new instance to backup.
        :param instance: The instance to backup.
        :return: None
        """

        instance_working_dir = instance.working_directory()
        instance_backup_dir = (
            instance_working_dir / self._options.backup_dir
        ).resolve()
        if not instance_backup_dir.is_relative_to(instance_working_dir.resolve()):
            logger.error(
                "Backup directory cannot be outside of instance working directory, aborting submission!"
            )
            return

        self.instances[instance.uuid] = instance
        self.load_saved_backups(instance=instance)
        self._initialize_recurring_job(instance=instance)

    def load_saved_backups(self, instance: "BaseInstance"):
        self.backup_dir_sizes[instance.uuid] = 0

        instance_backup_dir = instance.working_directory() / self._options.backup_dir

        if not instance_backup_dir.exists():
            return

        for file in instance_backup_dir.iterdir():
            if not file.is_file():
                continue

            self.backup_dir_sizes[instance.uuid] += file.stat().st_size
