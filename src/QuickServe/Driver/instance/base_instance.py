"""
Class for deployed service instances.

Author: Quintin Dunn
Date: 09/14/2026
"""

from dataclasses import dataclass
from uuid import UUID
from pathlib import Path

from QuickServe.Driver.utils import sanitize_filename

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServe.FileSystem.path_resolver import Workspace
    from QuickServe.FileSystem.modules import Module


@dataclass(slots=True)
class BaseInstance:
    module: "Module"
    service_name: str
    uuid: UUID
    module_name: str
    workspace: "Workspace"

    def working_directory(self) -> Path:
        """
        Ensures and gets the working directory for this instance.

        :return: The instance working directory.
        """
        dir_name = sanitize_filename(f"{self.uuid.hex[:16]}-{self.service_name}")
        return self.workspace.ensure_directory(f"services/{dir_name}")
