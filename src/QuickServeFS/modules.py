from pathlib import Path

class Module:
    path: Path

    def __init__(self, module_path: str | Path):
        self.path = Path(module_path)
