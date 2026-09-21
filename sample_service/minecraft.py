"""
Module main class for generating Minecraft Vanilla servers.

Author: Quintin Dunn
Date: 09/09/2026
"""

import json
import os
import signal
import threading
import logging

from typing import TYPE_CHECKING, Callable
from uuid import UUID

import requests

from .downloader import Downloader
from .server import MinecraftServer

from QuickServeServiceLibrary.decorators import instance_specific

if TYPE_CHECKING:
    from QuickServe.FileSystem.modules import Module
    from QuickServe.Driver.instance.base_instance import BaseInstance
    from QuickServe.Application.instances import InstanceService
    from QuickServe.Runtimes.runtime_manager import RuntimeManager

logger = logging.getLogger("minecraft-vanilla")


class Service:
    NAME: str = "Minecraft-Vanilla"
    VERSION: str = "0.0.1"
    QUICKSERVE_VERSION: str = "0.0.1"
    AUTHORS: list[dict] = [
        {"name": "Quintin Dunn", "github": "https://github.com/quintindunn"}
    ]
    PAGES: list[str] = ["about", "create", "start", "filesystem"]

    module: "Module"
    runtime_manager: "RuntimeManager"
    downloader: "Downloader"
    ws_send_callback: Callable

    instance_server_map: dict[UUID, MinecraftServer]
    instance_callback_map: dict[UUID, Callable]

    def __init__(self, module: "Module", runtime_manager: "RuntimeManager"):
        logger.info(f"Loading service: {self.NAME}")
        self.module = module
        self.downloader = Downloader()
        self.versions = [
            version for version in self.downloader.version_manifest.versions.keys()
        ]
        self.downloader.get_release_manifest("1.8.9")
        self.runtime_manager = runtime_manager
        self.instance_server_map = dict()
        self.instance_callback_map = dict()

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

    def action_install(self, instances: "InstanceService", **kwargs):
        """
        Installation action
        :param instances: InstanceService reference, used for record insertion
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

        manifest = self.downloader.get_release_manifest(id_=minecraft_version)
        jar_url = manifest.server.url
        java_major = manifest.java.major_version

        instance = instances.new_service(
            module_name=self.NAME, service_name=instance_name
        )

        cwd = instance.working_directory()
        with open(cwd / "jre-requirements", "w") as f:
            f.write(str(java_major))

        server_dir = cwd / "server"
        self.module.workspace.ensure_directory(server_dir)

        with open(server_dir / "server.jar", "wb") as f:
            request = requests.get(jar_url, stream=True)
            request.raise_for_status()

            for chunk in request.iter_content(chunk_size=1024 * 1024 * 10):
                f.write(chunk)

        with open(server_dir / "eula.txt", "w") as f:
            f.write("eula=true")

        return "start", 302, instance

    def on_message(self, msg: str, instance: "BaseInstance") -> None:
        msg = json.loads(msg)
        is_simple_controller = msg.get("isSimpleController") == True
        if not is_simple_controller:
            return

        msg_type = msg.get("type")

        server = self.instance_server_map.get(instance.uuid)

        if msg_type == "start":
            self.on_start(instance=instance)
        elif (server is None) or (not server.is_running):
            return
        elif msg_type == "stop":
            self.on_stop(instance=instance)
        elif msg_type == "kill":
            self.on_kill(instance=instance)
        elif msg_type == "command":
            self.on_command(instance=instance, command=msg.get("raw"))

    def on_start(self, instance: "BaseInstance"):
        server = self.instance_server_map.get(instance.uuid)
        if server is not None and server.is_running:
            logger.info("Server already running. ")
            return

        # Get Java Requirements
        jre_requirements_path = instance.working_directory() / "jre-requirements"
        assert jre_requirements_path.exists()

        with open(jre_requirements_path, "r") as f:
            jre_requirement = int(f.read())

        java_executable = self.runtime_manager.get_java_executable(
            jre_requirement, "jre"
        )

        if instance.uuid in self.instance_server_map:
            server = self.instance_server_map[instance.uuid]
            if not server.is_running:
                server.start(java_executable=java_executable)
                return

        server = MinecraftServer(instance.working_directory() / "server")
        self.instance_server_map[instance.uuid] = server
        server.start(java_executable=java_executable)

        callback = self.instance_callback_map.get(instance.uuid)
        if callback is None:
            logger.warning("No callback!")
            return

        def stdout_read():
            for line in iter(server.proc.stdout.readline, ""):
                callback(line)

        def stderr_read():
            for line in iter(server.proc.stderr.readline, ""):
                callback(line)

        def proc_read():
            threading.Thread(target=stdout_read, daemon=True).start()
            threading.Thread(target=stderr_read, daemon=True).start()

        proc_read()

    def on_kill(self, instance: "BaseInstance"):
        logger.info("Killing server")
        server = self.instance_server_map.get(instance.uuid)
        if server.is_running:
            logger.info(f"Killing process with PID {server.proc.pid}")
            os.kill(server.proc.pid, signal.SIGKILL)
            print(server.proc.returncode)

    def on_stop(self, instance: "BaseInstance"):
        logger.info("Stopping server")
        server = self.instance_server_map.get(instance.uuid)
        if server is None or not server.is_running:
            return

        server.proc.stdin.write("stop\n")
        server.proc.stdin.flush()

    def on_command(self, instance: "BaseInstance", command: str):
        server = self.instance_server_map.get(instance.uuid)
        if server is None or not server.is_running:
            return

        server.proc.stdin.write(command)
        server.proc.stdin.flush()

    @instance_specific
    def start(
        self, instance: "BaseInstance", send_callback: Callable
    ) -> tuple[str, dict]:
        asset = self.module.get_resource_path("start.html")
        self.instance_callback_map[instance.uuid] = send_callback

        with open(asset, "r") as f:
            return f.read(), {"versions": self.versions}

    @instance_specific
    def filesystem(self, instance: "BaseInstance", *args, **kwargs):
        asset = self.module.get_resource_path("filesystem.html")

        with open(asset, "r") as f:
            return f.read(), dict()
