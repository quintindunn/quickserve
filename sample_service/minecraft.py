import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeFS.modules import Module

logger = logging.getLogger("minecraft-vanilla")


class Service:
    NAME: str = "Minecraft-Vanilla"
    VERSION: str = "0.0.1"
    QUICKSERVE_VERSION: str = "0.0.1"

    module: "Module"

    def __init__(self, module: "Module"):
        logger.info(f"Loading service: {self.NAME}")
        self.module = module

    def about(self) -> str:
        """HTML about for the page"""

        asset = self.module.get_resource_path("about.html")
        with open(asset, "r") as f:
            return f.read()
