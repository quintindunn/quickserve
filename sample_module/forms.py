from QuickServeModuleLibrary.forms.datatypes import String
from QuickServeModuleLibrary.forms.forms import QSForm


class BanPlayer(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    playerName = String(placeholder="Player Name", required=True)
    banReason = String(placeholder="Ban Reason", required=False)


class BanIp(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    ip = String(placeholder="IP Address", required=True)
    banReason = String(placeholder="Ban Reason", required=False)


class UnBanPlayer(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    playerName = String(placeholder="Player Name", required=True)


class UnBanIP(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    ip = String(placeholder="IP Address", required=True)


class OpPlayer(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    username = String(placeholder="Username", required=True)


class DeOpPlayer(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    username = String(placeholder="Username", required=True)


class WhitelistPlayer(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    username = String(placeholder="Username", required=True)


class WhitelistRemove(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    username = String(placeholder="Username", required=True)