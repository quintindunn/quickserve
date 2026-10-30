"""
Module main class for generating Minecraft Vanilla servers.

Author: Quintin Dunn
Date: 09/09/2026
"""

import logging

from typing import TYPE_CHECKING, Callable

import requests

from QuickServeModuleLibrary.process import ManagedProcess
from QuickServeModuleLibrary.simple_controller import SimpleControllerProcessManager
from QuickServeModuleLibrary.decorators import page, action

from .downloader import Downloader, VersionManifestReleaseTypeEnum
from .forms import (
    BanIp,
    BanPlayer,
    UnBanIP,
    UnBanPlayer,
    OpPlayer,
    DeOpPlayer,
    WhitelistPlayer,
    WhitelistRemove,
)

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
    DESCRIPTION: str = "Create a Minecraft Java Edition Vanilla Server!"
    FS_ROOT: str = "server"
    SUPPORTED_OPERATING_SYSTEMS: list[str] = ["Darwin", "Linux"]

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

        self.simple_controller_process_manager = SimpleControllerProcessManager(self)

    @page(page_name="about")
    def about(self, *_, **__) -> str:
        """HTML about for the page"""

        asset = self.module.get_resource_path("about.html")
        with open(asset, "r") as f:
            return f.read()

    @page(page_name="create")
    def create(self, *_, **__) -> tuple[str, dict]:
        """HTML create for the page"""

        asset = self.module.get_resource_path("create.html")
        with open(asset, "r") as f:
            return f.read(), {"versions": self.versions}

    @action
    def install(self, instances: "InstanceManager", **kwargs):
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
            command=command,
            base_module=self.module,
            root_dir=instance.working_directory() / "server",
            history_buffer_flush_interval=20,
        )
        process.on_stderr(send_callback)
        process.on_stdout(send_callback)
        return process

    def on_message(self, msg: str, instance: "BaseInstance") -> None:
        self.simple_controller_process_manager.on_message(msg=msg, instance=instance)

    @page(instance_specific=True, page_name="start")
    def start(
        self, instance: "BaseInstance", send_callback: Callable
    ) -> tuple[str, dict]:
        asset = self.module.get_resource_path("start.html")

        if not self.simple_controller_process_manager.has_instance(instance=instance):
            self.simple_controller_process_manager.register(
                instance=instance,
                process=self.build_process(
                    instance=instance, send_callback=send_callback
                ),
            )
        with open(asset, "r") as f:
            return f.read(), {"versions": self.versions}

    @page(instance_specific=True, page_name="file manager")
    def filesystem(self, instance: "BaseInstance", *args, **kwargs):
        asset = self.module.get_resource_path("filesystem.html")

        with open(asset, "r") as f:
            return f.read(), dict()

    @page(instance_specific=True, page_name="Player Management")
    def player_management(self, instance: "BaseInstance", *args, **kwargs):
        asset = self.module.get_resource_path("management.html")

        context = {
            "forms": {
                "ban_player": BanPlayer(
                    action_name="ban-player-action", instance_uuid=str(instance.uuid)
                ).compile(submit_text="Ban Player"),
                "ban_ip": BanIp(
                    action_name="ban-ip-action", instance_uuid=str(instance.uuid)
                ).compile(submit_text="Ban IP"),
                "unban_player": UnBanPlayer(
                    action_name="unban-player-action", instance_uuid=str(instance.uuid)
                ).compile(submit_text="Unban Player"),
                "unban_ip": UnBanIP(
                    action_name="unban-ip-action", instance_uuid=str(instance.uuid)
                ).compile(submit_text="Unban IP"),
                "whitelist_add": WhitelistPlayer(
                    action_name="whitelist-add-action", instance_uuid=str(instance.uuid)
                ).compile(submit_text="Whitelist Player"),
                "whitelist_remove": WhitelistRemove(
                    action_name="whitelist-remove-action",
                    instance_uuid=str(instance.uuid),
                ).compile(submit_text="Unwhitelist Player"),
                "op": OpPlayer(
                    action_name="op-action", instance_uuid=str(instance.uuid)
                ).compile(submit_text="OP player"),
                "deop": DeOpPlayer(
                    action_name="deop-action", instance_uuid=str(instance.uuid)
                ).compile(submit_text="DeOP player"),
            }
        }

        with open(asset, "r") as f:
            return f.read(), context

    def execute_command(self, instance: "BaseInstance", args: list[str]) -> bool:
        process = self.simple_controller_process_manager.get_process(instance=instance)
        if process is None:
            logger.warning("No process for instance %s!", instance.uuid)
            return False
        for arg in args:
            if " " in arg:
                logger.warning("Space in argument!")
                return False

        command = " ".join(args) + "\n"
        process.write(command.encode())
        return True

    @action(action_name="ban-player-action")
    def ban_player_action(self, instances: "InstanceManager", **kwargs):
        form = BanPlayer.response_from_request(kwargs)
        instance = instances.from_uuid(form.instance_uuid.response)

        command = ["ban", form.playerName.response]
        if form.banReason.response:
            command.append(form.banReason.response)

        logger.info(
            "Command %s - %s", repr(command), self.execute_command(instance, command)
        )

        return "Player Management", 302, instance

    @action(action_name="ban-ip-action")
    def ban_ip_action(self, instances: "InstanceManager", **kwargs):
        form = BanIp.response_from_request(kwargs)
        instance = instances.from_uuid(form.instance_uuid.response)

        command = ["ban-ip", form.ip.response]
        if form.banReason.response:
            command.append(form.banReason.response)

        logger.info(
            "Command %s - %s", repr(command), self.execute_command(instance, command)
        )

        return "Player Management", 302, instance

    @action(action_name="unban-player-action")
    def unban_player_action(self, instances: "InstanceManager", **kwargs):
        form = UnBanPlayer.response_from_request(kwargs)
        instance = instances.from_uuid(form.instance_uuid.response)

        command = ["pardon", form.playerName.response]
        logger.info(
            "Command %s - %s", repr(command), self.execute_command(instance, command)
        )

        return "Player Management", 302, instance

    @action(action_name="unban-ip-action")
    def unban_ip_action(self, instances: "InstanceManager", **kwargs):
        form = UnBanIP.response_from_request(kwargs)
        instance = instances.from_uuid(form.instance_uuid.response)

        command = ["pardon-ip", form.ip.response]
        logger.info(
            "Command %s - %s", repr(command), self.execute_command(instance, command)
        )

        return "Player Management", 302, instance

    @action(action_name="whitelist-add-action")
    def whitelist_add_action(self, instances: "InstanceManager", **kwargs):
        form = WhitelistPlayer.response_from_request(kwargs)
        instance = instances.from_uuid(form.instance_uuid.response)

        command = ["whitelist", "add", form.username.response]
        logger.info(
            "Command %s - %s", repr(command), self.execute_command(instance, command)
        )

        return "Player Management", 302, instance

    @action(action_name="whitelist-remove-action")
    def whitelist_remove_action(self, instances: "InstanceManager", **kwargs):
        form = WhitelistRemove.response_from_request(kwargs)
        instance = instances.from_uuid(form.instance_uuid.response)

        command = ["whitelist", "remove", form.username.response]
        logger.info(
            "Command %s - %s", repr(command), self.execute_command(instance, command)
        )

        return "Player Management", 302, instance

    @action(action_name="op-action")
    def op_player_action(self, instances: "InstanceManager", **kwargs):
        form = OpPlayer.response_from_request(kwargs)
        instance = instances.from_uuid(form.instance_uuid.response)

        command = ["op", form.username.response]
        logger.info(
            "Command %s - %s", repr(command), self.execute_command(instance, command)
        )

        return "Player Management", 302, instance

    @action(action_name="deop-action")
    def deop_player_action(self, instances: "InstanceManager", **kwargs):
        form = DeOpPlayer.response_from_request(kwargs)
        instance = instances.from_uuid(form.instance_uuid.response)

        command = ["deop", form.username.response]
        logger.info(
            "Command %s - %s", repr(command), self.execute_command(instance, command)
        )

        return "Player Management", 302, instance
