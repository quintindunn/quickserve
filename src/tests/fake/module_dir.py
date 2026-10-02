import logging
import shutil
from pathlib import Path

from QuickServe.FileSystem.path_resolver import Workspace
from tests.fake import mymodule

logger = logging.getLogger(__name__)

def setup_modules(workspace: "Workspace", folder_name_modifier: str = "") -> None:
    root = workspace.ensure_directory("modules")
    module_folder = Path(mymodule.__file__).parent
    logger.info(f"Setting up modules from {module_folder}")
    shutil.copytree(module_folder, root / (module_folder.name + folder_name_modifier))
