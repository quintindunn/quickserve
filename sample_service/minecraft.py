import logging
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from QuickServeFS.modules import Module

logger = logging.getLogger("minecraft-vanilla")


class Service:
    NAME: str = "Minecraft-Vanilla"
    VERSION: str = "0.0.1"
    QUICKSERVE_VERSION: str = "0.0.1"
    AUTHORS: list[dict] = [
        {"name": "Quintin Dunn", "github": "https://github.com/quintindunn"}
    ]

    module: "Module"

    def __init__(self, module: "Module"):
        logger.info(f"Loading service: {self.NAME}")
        self.module = module

    def about(self) -> str:
        """HTML about for the page"""

        asset = self.module.get_resource_path("about.html")
        with open(asset, "r") as f:
            return f.read()

    def create(self) -> tuple[str, dict]:
        """HTML create for the page"""

        asset = self.module.get_resource_path("create.html")
        with open(asset, "r") as f:
            return f.read(), {
                "versions": [
                    "1.8.9",
                    "1.9.0",
                    "1.9.1",
                    "1.10.0",
                    "1.10.2",
                    "1.11.1",
                    "1.12.2",
                ]
            }

    def install(self, *args, **kwargs):
        print(kwargs)
        logger.info(
            f"Installing new minecraft-vanilla instance with version {kwargs['minecraft-version']} with name {kwargs['instance-name']}"
        )

        return "about", 200
