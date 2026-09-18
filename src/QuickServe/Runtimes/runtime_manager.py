"""
Manager for different runtime environments

Author: Quintin Dunn
Date: 09/18/2026
"""

import os
import platform
import shutil
import subprocess
import sys
import uuid
import logging

from pathlib import Path

import requests

from QuickServe.FileSystem.path_resolver import Workspace


logger = logging.getLogger(__name__)

JRE_API_ROOT = "https://api.adoptium.net/"

JRE_ARCH_MAP = {"64bit": "x64", "32bit": "x32"}

JRE_OS_MAP = {
    "Windows": "windows",
    "Darwin": "mac",
    "Linux": "linux",
}


class RuntimeManager:
    def __init__(self, workspace: "Workspace"):
        self.workspace = workspace
        self.workspace.ensure_directory("runtimes")

    def _get_jre_root(self, major_version: int, image_type: str):
        """
        Gets the root to where the JRE is located.
        :param major_version: JRE major version
        :param image_type: JRE component
        :return:
        """

        return self.workspace.get_path(
            Path("runtimes") / "jre" / f"{major_version}-{image_type}"
        )

    def check_jre_exists(self, major_version: int, image_type: str) -> bool:
        """
        Checks if a given JRE is already installed.
        :param major_version: JRE major version
        :param image_type: JRE component
        :return: True if JRE exists, False if not.
        """
        root = self._get_jre_root(major_version=major_version, image_type=image_type)
        if not root.exists():
            return False
        if not (root / "bin").exists():
            return False
        try:
            next((root / "bin").glob("java"))
        except StopIteration:
            return False

        return True

    def ensure_jre(self, major_version: int, image_type: str) -> Path:
        """
        Ensures a JRE exists, if it doesn't, installs it.
        :param major_version: JRE major version
        :param image_type: JRE component
        :return: The path to JRE root.
        """

        logger.info(f"Checking if JRE for {major_version}-{image_type} exists.")
        jre_root = self._get_jre_root(
            major_version=major_version, image_type=image_type
        )
        if self.check_jre_exists(major_version=major_version, image_type=image_type):
            logger.info(f"JRE {major_version}-{image_type} exists.")
            logger.debug(
                f"JRE root: {self._get_jre_root(major_version=major_version, image_type=image_type)!r}"
            )
            return jre_root

        jre_download_link = self.get_jre_download_link(
            major_version=major_version, image_type=image_type
        )
        file_type = jre_download_link.split(".")[-1]

        logger.info(f"JRE Download link: {jre_download_link!r}")

        tmp_dir = self.workspace.ensure_directory("tmp")
        file_name = f"{uuid.uuid4()}-JRE.{file_type}"
        with open(tmp_dir / file_name, "wb") as f:
            logger.info("Downloading JRE.")
            request = requests.get(jre_download_link, stream=True)

            for chunk in request.iter_content(chunk_size=1024 * 1024 * 10):  # 10mb
                f.write(chunk)

        self.install_jre(
            tmp_location=tmp_dir / file_name,
            major_version=major_version,
            image_type=image_type,
        )

        return jre_root

    def get_jre_download_link(
        self,
        major_version: int,
        image_type: str,
        arch: str | None = None,
        operating_system: str | None = None,
    ) -> str:
        """
        Gets the download link for a JRE.
        Useful Link: https://api.adoptium.net/q/swagger-ui/#/Assets/searchReleases

        :param major_version: The major version of the JRE
        :param image_type: The image type for the JRE.
        :param arch: The architecture for the JRE, if None it will be determined by the host.
        :param operating_system: The operating system for the JRE, if None it will be determined by the host.
        :return:
        """

        if arch is None:
            arch = JRE_ARCH_MAP.get(platform.architecture()[0])
            if arch is None:
                raise NotImplementedError(
                    f"Architecture {platform.architecture()} is not supported."
                )

        if operating_system is None:
            operating_system = JRE_OS_MAP.get(platform.system())
            if operating_system is None:
                raise NotImplementedError(f"OS {platform.system()} is not supported.")

        url = f"{JRE_API_ROOT}/v3/assets/feature_releases/{major_version}/ga"
        request = requests.get(
            url,
            params={
                "architecture": arch,
                "image_type": image_type,
                "os": operating_system,
                "project": "jdk",
                "page_size": 1,
            },
        )
        request.raise_for_status()

        binary_link = request.json()[0]["binaries"][0]["installer"]["link"]

        return binary_link

    def install_jre(self, tmp_location: Path, major_version: int, image_type: str):
        operating_system = platform.system()

        if operating_system == "Darwin":
            self.install_jre_macos(
                tmp_location=tmp_location,
                major_version=major_version,
                image_type=image_type,
            )
        elif operating_system == "Linux":
            self.install_jre_linux(
                tmp_location=tmp_location,
                major_version=major_version,
                image_type=image_type,
            )
        elif operating_system == "Windows":
            self.install_jre_windows(
                tmp_location=tmp_location,
                major_version=major_version,
                image_type=image_type,
            )

    def install_jre_macos(
        self, tmp_location: Path, major_version: int, image_type: str
    ) -> None:
        """
        Installs a JRE to the /opt/quickserve/runtimes/jre/x-x directory.
        :param tmp_location: The location of the .pkg file from Adoptium
        :param major_version: The major version of the JRE
        :param image_type: The image type, same as the one used to download in RuntimeManager.ensure_jre
        :return: None
        """
        logger.info(
            f"Install JRE {major_version}-{image_type} for Macos from {tmp_location}."
        )

        # Step 1.) unpack temp file
        unpacked_location = self.workspace.get_path(f"tmp/{uuid.uuid4()}")
        logger.debug(f"Unpacking {tmp_location} to {unpacked_location}")
        command = [
            "pkgutil",
            "--expand-full",
            tmp_location,
            unpacked_location.absolute(),
        ]
        proc = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        proc.wait()
        if proc.returncode != 0:
            stdout, stderr = proc.communicate()
            raise RuntimeError(
                f"Error unpacking JRE archive:\n\tSTDOUT: {stdout.decode()!r}\n\tSTDERR:{stderr.decode()!r}"
            )

        # Step 2.) Find secondary binary folder.
        step_1 = (
            next(unpacked_location.glob("*.pkg"))
            / "Payload"
            / "Library"
            / "Java"
            / "JavaVirtualMachines"
        )
        contents_folder = step_1 / os.listdir(step_1)[0] / "Contents"
        binary_folder = contents_folder / "Home"
        logger.debug(f"Located binary folder {binary_folder}")

        jre_root = self._get_jre_root(
            major_version=major_version, image_type=image_type
        )
        if jre_root.exists():
            logger.info("Found pre-existing installation, uninstalling.")
            shutil.rmtree(jre_root)
            os.rmdir(jre_root)

        logger.info(f"Copying environment")
        shutil.copytree(binary_folder, jre_root)

        logger.info("Cleaning up.")
        shutil.rmtree(binary_folder)
        shutil.rmtree(unpacked_location)
        os.remove(tmp_location)

    def install_jre_linux(
        self, tmp_location: Path, major_version: int, image_type: str
    ) -> None:
        """
        NOT IMPLEMENTED

        Installs the JRE for linux to <QUICKSERVE_ROOT>/runtimes/jre/x-x/
        :param tmp_location: The location of the .pkg file from Adoptium
        :param major_version: The major version of the JRE
        :param image_type: The image type, same as the one used to download in RuntimeManager.ensure_jre
        :return: None
        """

        raise NotImplementedError("JRE Installer for linux not yet supported")

    def install_jre_windows(
        self, tmp_location: Path, major_version: int, image_type: str
    ) -> None:
        """
        NOT IMPLEMENTED

        Installs the JRE for windows to <QUICKSERVE_ROOT>/runtimes/jre/x-x/
        :param tmp_location: The location of the .pkg file from Adoptium
        :param major_version: The major version of the JRE
        :param image_type: The image type, same as the one used to download in RuntimeManager.ensure_jre
        :return: None
        """

        raise NotImplementedError("JRE Installer for windows not yet supported")

    def get_java_executable(
        self, major_version: int, image_type: str, install_missing: bool = True
    ):
        exists = self.check_jre_exists(
            major_version=major_version, image_type=image_type
        )
        if not exists and install_missing:
            logger.info(f"{image_type.upper()} {major_version} not found. Installing.")
            self.ensure_jre(major_version=major_version, image_type=image_type)

        logger.info("Verifying JRE exists.")
        exists = self.check_jre_exists(
            major_version=major_version, image_type=image_type
        )
        if not exists:
            raise FileNotFoundError("No Java executable found!")

        root = self.workspace.get_path(
            self._get_jre_root(major_version=major_version, image_type=image_type)
        )

        operating_system = platform.system()

        if operating_system == "Darwin":
            return root / "bin" / "java"
        elif operating_system == "Windows":
            raise NotImplementedError(
                f"Getting executable for {operating_system} is not supported yet."
            )
        elif operating_system == "Linux":
            raise NotImplementedError(
                f"Getting executable for {operating_system} is not supported yet."
            )
        else:
            raise NotImplementedError(
                f"Operating system {operating_system!r} is not supported."
            )


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    workspace_ = Workspace()
    runtime_manager = RuntimeManager(workspace=workspace_)
    executable = runtime_manager.get_java_executable(8, "jre")
    print(executable)
