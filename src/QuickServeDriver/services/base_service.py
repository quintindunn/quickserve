import uuid

from pathlib import Path

from QuickServeDriver.utils import sanitize_filename

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from QuickServeFS.config import Config

class BaseService:
    cfg: "Config"
    service_name: str
    uuid: str

    def __init__(self, cfg: "Config", service_name: str):
        self.cfg = cfg
        self.service_name = service_name
        self.uuid = uuid.uuid4().hex

    def working_directory(self) -> Path:
        dir_name = sanitize_filename(f"{self.uuid[:16]}-{self.service_name}")
        return self.cfg.resolver.ensure_file_path(f"services/{dir_name}")

if __name__ == '__main__':
    from QuickServeFS import config
    service = BaseService(cfg=config, service_name="Minecraft1.8.9")
    print(service.working_directory())