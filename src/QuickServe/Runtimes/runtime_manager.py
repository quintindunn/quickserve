import platform
import sys
import uuid
from pathlib import Path

import requests

from QuickServe.FileSystem.path_resolver import Workspace

import logging

logger = logging.getLogger(__name__)

JRE_API_ROOT = "https://api.adoptium.net/"

JRE_ARCH_MAP = {"64bit": "x64"}

JRE_OS_MAP = {
    "Windows": "windows",
    "Darwin": "mac",
    "Linux": "linux",
}


class RuntimeManager:
    def __init__(self, workspace: "Workspace"):
        self.workspace = workspace
        self.workspace.ensure_directory("runtimes")

    @staticmethod
    def _get_jre_root(major_version: int, component: str):
        """
        Gets the root to where the JRE is located.
        :param major_version: JRE major version
        :param component: JRE component
        :return:
        """
        return Path("runtimes") / f"{major_version}-{component}"

    def check_jre_exists(self, major_version: int, component: str) -> bool:
        """
        Checks if a given JRE is already installed.
        :param major_version: JRE major version
        :param component: JRE component
        :return: True if JRE exists, False if not.
        """
        # TODO: Add validation JRE is installed correctly
        return self._get_jre_root(
            major_version=major_version, component=component
        ).exists()

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

        if operating_system == "Drawin":
            self.install_jre_macos(tmp_location=tmp_location, major_version=major_version, image_type=image_type)
        elif operating_system == "Linux":
            self.install_jre_linux(tmp_location=tmp_location, major_version=major_version, image_type=image_type)
        elif operating_system == "Windows":
            self.install_jre_windows(tmp_location=tmp_location, major_version=major_version, image_type=image_type)

    def install_jre_macos(self, tmp_location: Path, major_version: int, image_type: str):
        logger.info(f"Install JRE {major_version}-{image_type} for Macos from {tmp_location}.")

    def install_jre_linux(self, tmp_location: Path, major_version: int, image_type: str): raise NotImplementedError("JRE Installer for linux not supported")

    def install_jre_windows(self, tmp_location: Path, major_version: int, image_type: str): raise NotImplementedError("JRE Installer for windows not supported")

    def ensure_jre(self, major_version: int, image_type: str) -> Path:
        """
        Ensures a JRE exists, if it doesn't, installs it.
        :param major_version: JRE major version
        :param image_type: JRE component
        :return: The path to JRE root.
        """
        logger.info(f"Checking if JRE for {major_version}-{image_type} exists.")
        jre_root = self._get_jre_root(major_version=major_version, component=image_type)
        if self.check_jre_exists(major_version=major_version, component=image_type):
            logger.info(f"JRE {major_version}-{image_type} exists.")
            logger.debug(
                f"JRE root: {self._get_jre_root(major_version=major_version, component=image_type)!r}"
            )
            return jre_root

        self.workspace.ensure_directory(
            self._get_jre_root(major_version=major_version, component=image_type)
        )

        jre_download_link = self.get_jre_download_link(8, "jre")
        file_type = jre_download_link.split(".")[-1]

        logger.info(f"JRE Download link: {jre_download_link!r}")

        tmp_dir = self.workspace.ensure_directory("tmp")
        file_name = f"{uuid.uuid4()}-JRE.{file_type}"
        with open(tmp_dir / file_name, 'wb') as f:
            request = requests.get(jre_download_link, stream=True)

            for chunk in request.iter_content(chunk_size=1024*1024*10):
                f.write(chunk)

        self.install_jre(tmp_location=tmp_dir / file_name, major_version=major_version, image_type=image_type)

        return jre_root


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    workspace = Workspace("/opt/quickserve")
    runtime_manager = RuntimeManager(workspace=workspace)
    jre_location = runtime_manager.ensure_jre(8, "jre")
    print(jre_location)