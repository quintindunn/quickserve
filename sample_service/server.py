from pathlib import Path


class MinecraftServer:
    root_dir: Path
    jar: Path
    is_running: bool

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.jar = root_dir / "server.jar"
        self.is_running = False

    def check_eula(self):
        with open(self.root_dir / "eula.txt") as f:
            lines = f.readlines()
        for line in lines:
            if line == "eula=true":
                return True
        return False

    def validate(self):
        assert self.root_dir.exists()
        assert (self.root_dir / "server.jar").exists()
        assert self.check_eula()
