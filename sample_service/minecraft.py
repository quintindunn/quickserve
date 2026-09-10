"""
Module main class for generating Minecraft Vanilla servers.

Author: Quintin Dunn
Date: 09/09/2026
"""

import logging

from typing import TYPE_CHECKING, Union

import requests

from .downloader import Downloader

if TYPE_CHECKING:
    from QuickServeFS.modules import Module
    from QuickServeDriver.instance.base_instance import BaseInstance

logger = logging.getLogger("minecraft-vanilla")

####################################################################
# START TEMP LOCATION (I'm too lazy to set up a package right now) #
####################################################################
import asyncio
from collections.abc import Awaitable, Callable

import websockets
from websockets.asyncio.server import ServerConnection

from functools import wraps

MessageHandler = Callable[[str, "SimpleController"], Awaitable[None]]
ConnectionHandler = Callable[["SimpleController"], Awaitable[None]]


class SimpleController:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self._on_message_registry: list[MessageHandler] = []
        self._on_connect_registry: list[ConnectionHandler] = []
        self._on_close_registry: list[ConnectionHandler] = []

    def on_message(self) -> Callable[[MessageHandler], MessageHandler]:
        def decorator(func: MessageHandler) -> MessageHandler:
            self._on_message_registry.append(func)
            return func

        return decorator

    def on_connect(self) -> Callable[[ConnectionHandler], ConnectionHandler]:
        def decorator(func: ConnectionHandler) -> ConnectionHandler:
            self._on_connect_registry.append(func)
            return func

        return decorator

    def on_close(self) -> Callable[[ConnectionHandler], ConnectionHandler]:
        def decorator(func: ConnectionHandler) -> ConnectionHandler:
            self._on_close_registry.append(func)
            return func

        return decorator

    async def _handle_connection(self, websocket: ServerConnection):
        self.websocket = websocket

        await self._on_connect()

        try:
            async for message in websocket:
                await self._on_message(message)
        finally:
            await self._on_close()

    async def _on_message(self, message: str):
        for func in self._on_message_registry:
            await func(message, self)

    async def _on_connect(self):
        for func in self._on_connect_registry:
            await func(self)

    async def _on_close(self):
        for func in self._on_close_registry:
            await func(self)

    async def send_message(self, message: str):
        await self.websocket.send(message)

    async def start(self):
        async with websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
        ):
            await asyncio.Future()


def instance_specific(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.instance is None:
            return (
                "<!DOCTYPE HTML>"
                "<html><head><title>404 Not Found!</title></head>"
                "<body><h1>Page not found!</h1></body></html>"
            )
        return func(self, *args, **kwargs)

    return wrapper


#####################
# END TEMP LOCATION #
#####################


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

    instance: Union["BaseInstance", None]

    def __init__(self, module: "Module", instance: Union["BaseInstance", None] = None):
        logger.info(f"Loading service: {self.NAME}")
        self.module = module
        self.downloader = Downloader()
        self.versions = [
            version for version in self.downloader.version_manifest.versions.keys()
        ]
        self.downloader.get_release_manifest("1.8.9")

        self.instance = instance

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
    def start(self) -> tuple[str, dict]:
        assert self.instance

        asset = self.module.get_resource_path("start.html")

        with open(asset, "r") as f:
            return f.read(), {"versions": self.versions}
