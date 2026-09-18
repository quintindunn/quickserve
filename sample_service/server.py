import logging
import subprocess
import time
from pathlib import Path
from subprocess import Popen

logger = logging.getLogger(__name__)


class MinecraftServer:
    root_dir: Path
    jar: Path

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.jar = root_dir / "server.jar"
        self.proc: Popen = None
        self.started_at = -1

    def check_eula(self):
        assert (self.root_dir / "eula.txt").exists()
        with open(self.root_dir / "eula.txt") as f:
            lines = f.readlines()
        for line in lines:
            if line == "eula=true":
                return True
        return False

    @property
    def is_running(self):
        if self.proc is None:
            return False
        poll = self.proc.poll()
        return poll is None

    def validate(self):
        assert self.root_dir.exists()
        assert (self.root_dir / "server.jar").exists()
        assert self.check_eula()

    def start(self, java_executable: Path, xmx: str = "4G", xms: str = "4G"):
        call_time = time.time()
        if (call_time - self.started_at) < 5:
            logger.info("Server might already be starting.")
            return

        self.started_at = call_time
        if self.is_running:
            logger.info("Server already running...")
            return

        command = [java_executable, f"-Xmx{xmx}", f"-Xms{xms}", "-jar", "./server.jar", "nogui"]
        logger.info(t"Starting server {command}")
        self.proc = subprocess.Popen(command,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     stdin=subprocess.PIPE,
                                     text=True,
                                     cwd=self.root_dir
                                     )
