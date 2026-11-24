import dataclasses
import json
from pathlib import Path
from typing import Any


@dataclasses.dataclass
class Entry:
    key: str
    value: str
    comment: str

    def set(self, value: Any):
        if isinstance(value, bool):
            self.value = str(value).lower()
            return
        self.value = value

    def get(self):
        return self.value

class PropertiesParser:
    def __init__(self, filepath: Path | str):
        self.filepath: Path = Path(filepath)

        self.lookup: dict[str, tuple[int, str]]
        self.lines: list[Entry] = list()
        self._parse()

    def _parse(self):
        with open(self.filepath, 'r') as f:
            for line in f:
                line = line.rstrip("\r\n")

                parts = line.split("#")
                if len(parts) == 1:
                    parts.append("")

                if parts[0]:
                    key, value = parts[0].split("=", 1)
                else:
                    key, value = "", ""

                entry = Entry(key=key, value=value, comment=parts[1])
                self.lines.append(entry)

    def reconstruct(self):
        output: list[str] = list()

        for entry in self.lines:
            line = ""
            if entry.key != "":
                line += f"{entry.key}={entry.value}"
            if entry.comment != "":
                line += f"{' ' if entry.key else ''}#{entry.comment}"
            output.append(line)

        return '\n'.join(output)

    def update(self):
        with open(self.filepath, 'w') as f:
            f.write(self.reconstruct())

    def __getitem__(self, item: str):
        for entry in self.lines:
            if entry.key == "":
                continue
            if entry.key == item:
                return entry
        raise KeyError(f"No argument {item!r} found!")

    def __iter__(self):
        for entry in self.lines:
            if entry.key:
                yield entry

    def __contains__(self, item):
        for i in self.__iter__():
            if item == i.key:
                return True
        return False
