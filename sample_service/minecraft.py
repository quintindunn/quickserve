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
        logger.info(f"Loading service: {self}")
        self.module = module

        asset_path = self.module.get_resource_path("foo.txt")

        with open(asset_path, "r") as f:
            print(f"Loaded {f.read()}")
