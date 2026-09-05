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
    module: Path

    def __init__(self, cfg: "Config", service_name: str, module: Path):
        self.cfg = cfg
        self.service_name = service_name
        self.uuid = uuid.uuid4().hex
        self.module = module

    def working_directory(self) -> Path:
        dir_name = sanitize_filename(f"{self.uuid[:16]}-{self.service_name}")
        return self.cfg.resolver.ensure_file_path(f"services/{dir_name}")
