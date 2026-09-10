"""
Module main class for generating Minecraft Vanilla servers.

Author: Quintin Dunn
Date: 09/09/2026
"""

from typing import TYPE_CHECKING

import logging
import requests

from QuickServeServiceLibrary.decorators import instance_specific
from QuickServeServiceLibrary.SimpleController import (
    simple_controller_manager,
    SimpleController,
)

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
    PAGES: list[str] = ["about", "create", "start"]

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

    def about(self, *_, **__) -> str:
        """HTML about for the page"""

        asset = self.module.get_resource_path("about.html")
        with open(asset, "r") as f:
            return f.read()

    def create(self, *_, **__) -> tuple[str, dict]:
        """HTML create for the page"""

        asset = self.module.get_resource_path("create.html")
        with open(asset, "r") as f:
            return f.read(), {"versions": self.versions}

    def action_install(self, base_instance: "BaseInstance", **kwargs):
        """
        Installation action
        :param base_instance: BaseInstance class reference, used for record insertion
        :param kwargs: Required Kwargs:
        - minecraft-version: A valid Minecraft version, listed in Minecraft version manifest v2
        (https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)
        - instance-name: The name of the service instance being created.
        :return: The routing to the 'about' page, response code 302.
        """
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

        cwd = instance.working_directory()
        server_dir = cwd / "server"
        self.module.resolver.ensure_directory(server_dir)

        with open(server_dir / "server.jar", "wb") as f:
            request = requests.get(jar_url, stream=True)
            request.raise_for_status()

            for chunk in request.iter_content(chunk_size=1024 * 1024 * 10):
                f.write(chunk)

        with open(server_dir / "eula.txt", "w") as f:
            f.write("eula=true")

        return "about", 302

    @instance_specific
    def start(self, instance: "BaseInstance") -> tuple[str, dict]:
        assert instance.assigned_port != -1
        controller: SimpleController = simple_controller_manager.get_controller(
            port=instance.assigned_port
        )
        asset = self.module.get_resource_path("start.html")
        with open(asset, "r") as f:
            return f.read(), {"versions": self.versions}
