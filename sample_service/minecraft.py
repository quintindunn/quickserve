import logging

from typing import TYPE_CHECKING

import requests

from .downloader import Downloader

if TYPE_CHECKING:
    from QuickServeFS.modules import Module
    from QuickServeDriver.instance.base_instance import BaseInstance

logger = logging.getLogger("minecraft-vanilla")


class Service:
    NAME: str = "Minecraft-Vanilla"
    VERSION: str = "0.0.1"
    QUICKSERVE_VERSION: str = "0.0.1"
    AUTHORS: list[dict] = [
        {"name": "Quintin Dunn", "github": "https://github.com/quintindunn"}
    ]

    module: "Module"
    downloader: "Downloader"

    def __init__(self, module: "Module"):
        logger.info(f"Loading service: {self.NAME}")
        self.module = module
        self.downloader = Downloader()
        self.versions = [
            version for version in self.downloader.version_manifest.versions.keys()
        ]
        self.downloader.get_release_manifest("1.8.9")

    def about(self) -> str:
        """HTML about for the page"""

        asset = self.module.get_resource_path("about.html")
        with open(asset, "r") as f:
            return f.read()

    def create(self) -> tuple[str, dict]:
        """HTML create for the page"""

        asset = self.module.get_resource_path("create.html")
        with open(asset, "r") as f:
            return f.read(), {"versions": self.versions}

    def install(self, base_instance: "BaseInstance", **kwargs):
        assert "minecraft-version" in kwargs
        assert "instance-name" in kwargs

        minecraft_version = kwargs["minecraft-version"]
        instance_name = kwargs["instance-name"]

        logger.info(
            f"Installing new minecraft-vanilla instance with version {kwargs['minecraft-version']} with name {kwargs['instance-name']}"
        )

        jar_url = self.downloader.get_release_manifest(id_=minecraft_version).server.url
        instance = base_instance.new_service(
            module=self.module, service_name=instance_name, module_name=self.NAME
        )

        with open(instance.working_directory() / "server.jar", 'wb') as f:
            request = requests.get(jar_url, stream=True)
            request.raise_for_status()

            for chunk in request.iter_content(chunk_size=1024 * 1024 * 10):
                f.write(chunk)


        return "about", 200
