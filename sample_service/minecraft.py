import logging

from typing import TYPE_CHECKING

from .downloader import Downloader

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
    downloader: "Downloader"

    def __init__(self, module: "Module"):
        logger.info(f"Loading service: {self.NAME}")
        self.module = module
        self.downloader = Downloader()
        self.versions = [version for version in self.downloader.version_manifest.versions.keys()]
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
            return f.read(), {
                "versions": self.versions
            }

    def install(self, *args, **kwargs):
        print(kwargs)
        logger.info(
            f"Installing new minecraft-vanilla instance with version {kwargs['minecraft-version']} with name {kwargs['instance-name']}"
        )

        return "about", 200
