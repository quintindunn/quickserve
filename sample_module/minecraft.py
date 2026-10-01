"""
Module main class for generating Minecraft Vanilla servers.

Author: Quintin Dunn
Date: 09/09/2026
"""

import logging

from typing import TYPE_CHECKING, Callable
from uuid import UUID

import requests

from QuickServeModuleLibrary.process import ManagedProcess
from QuickServeModuleLibrary.simple_controller import SimpleControllerProcessManager
from .downloader import Downloader, VersionManifestReleaseTypeEnum
from .server import MinecraftServer

from QuickServeModuleLibrary.decorators import instance_specific

if TYPE_CHECKING:
    from QuickServe.FileSystem.modules import BaseModule
    from QuickServe.Driver.instance.base_instance import BaseInstance
    from QuickServe.Application.instances import InstanceManager
    from QuickServe.Runtimes.runtime_manager import RuntimeManager

logger = logging.getLogger("minecraft-vanilla")


class Module:
    NAME: str = "Minecraft-Vanilla"
    VERSION: str = "0.0.1"
    QUICKSERVE_VERSION: str = "0.0.1"
    AUTHORS: list[dict] = [
        {"name": "Quintin Dunn", "github": "https://github.com/quintindunn"}
    ]
    PAGES: list[str] = ["about", "create", "start", "filesystem"]
    FS_ROOT: str = "server"

    module: "BaseModule"
    runtime_manager: "RuntimeManager"
    downloader: "Downloader"
    ws_send_callback: Callable

    simple_controller_process_manager: "SimpleControllerProcessManager"

    def __init__(self, module: "BaseModule", runtime_manager: "RuntimeManager"):
        logger.info(f"Loading module: {self.NAME}")
        self.module = module
        self.downloader = Downloader()
        self.versions = [
            {
                "is_release": version.type == VersionManifestReleaseTypeEnum.release,
                "id": id_,
            }
            for id_, version in self.downloader.version_manifest.versions.items()
        ]
        self.downloader.get_release_manifest("1.8.9")
        self.runtime_manager = runtime_manager

        self.simple_controller_process_manager = SimpleControllerProcessManager()

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

    def action_install(self, instances: "InstanceManager", **kwargs):
        """
        Installation action
        :param instances: InstanceManager reference, used for record insertion
        :param kwargs: Required Kwargs:
        - minecraft-version: A valid Minecraft version, listed in Minecraft version manifest v2
        (https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)
        - instance-name: The name of the instance being created.
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

        instance = instances.new_instance(
            module_name=self.NAME, instance_name=instance_name
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

    def build_process(
        self,
        instance: "BaseInstance",
        send_callback: Callable,
        xmx: str = "4G",
        xms: str = "4G",
    ):
        jre_requirements_path = instance.working_directory() / "jre-requirements"
        assert jre_requirements_path.exists()

        with open(jre_requirements_path, "r") as f:
            jre_requirement = int(f.read())

        java_executable = self.runtime_manager.get_java_executable(
            jre_requirement, "jre"
        )

        command = [
            java_executable,
            f"-Xmx{xmx}",
            f"-Xms{xms}",
            "-jar",
            "./server.jar",
            "nogui",
        ]
        process = ManagedProcess(
            command=command, root_dir=instance.working_directory() / "server"
        )
        process.on_stderr(send_callback)
        process.on_stdout(send_callback)
        return process

    def on_message(self, msg: str, instance: "BaseInstance") -> None:
        self.simple_controller_process_manager.on_message(msg=msg, instance=instance)

    @instance_specific
    def start(
        self, instance: "BaseInstance", send_callback: Callable
    ) -> tuple[str, dict]:
        asset = self.module.get_resource_path("start.html")
        self.instance_callback_map[instance.uuid] = send_callback

        if not self.simple_controller_process_manager.has_instance(instance=instance):
            self.simple_controller_process_manager.register(
                instance=instance,
                process=self.build_process(
                    instance=instance, send_callback=send_callback
                ),
            )

        with open(asset, "r") as f:
            return f.read(), {"versions": self.versions}

    @instance_specific
    def filesystem(self, instance: "BaseInstance", *args, **kwargs):
        asset = self.module.get_resource_path("filesystem.html")

        with open(asset, "r") as f:
            return f.read(), dict()
