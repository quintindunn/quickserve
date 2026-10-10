"""
ManagedProcesses for easy integration with modules

Author: Quintin Dunn
Date: 10/10/2026
"""

from pathlib import Path
from subprocess import Popen, PIPE
from typing import Callable, Tuple

from threading import Thread, RLock

import signal
import os

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServe.FileSystem.modules import BaseModule


class ManagedProcess:
    """
    Creates processes with easy to handle stdio, start, stop
    """

    proc: Popen | None
    _on_stdout: list[Callable[[bytes], None]]
    _on_stderr: list[Callable[[bytes], None]]
    command: str
    root_dir: Path | None
    base_module: "BaseModule"

    def __init__(self, command, base_module: "BaseModule", root_dir: Path | None = None, history_buffer_flush_interval: int = 20):
        self.command = command
        self.base_module = base_module
        self.proc = None
        self._on_stderr = list()
        self._on_stdout = list()
        self.root_dir = root_dir
        self.lines_buffer = []
        self.line_buffer_lock = RLock()
        self.history_buffer_flush_interval = history_buffer_flush_interval

    def save_stdout(self, stdout: bytes) -> None:
        """
        Saves stdout for retrieval later for terminal history
        :param stdout: The raw stdout in bytes.
        :return: None
        """

        self._save_stdio(b"stdout", stdout)

    def save_stderr(self, stderr: bytes) -> None:
        """
        Saves stderr for retrieval later for terminal history
        :param stderr: The raw stdout in bytes.
        :return: None
        """

        self._save_stdio(b"stderr", stderr)

    def save_stdin(self, stdin: bytes) -> None:
        """
        Saves stdin for retrieval later for terminal history
        :param stdin: The raw stdout in bytes.
        :return: None
        """

        self._save_stdio(b"stdin", stdin)

    def _save_stdio(self, io_type: bytes, data: bytes) -> None:
        """
        Saves stdio for retrieval later for terminal history
        :param io_type: The type of stdio (stdout, stderr, stdin)
        :param data: The data being stored.
        :return: None
        """

        line = b"%b:::%b" % (io_type, data)
        self.lines_buffer.append(line)
        if len(self.lines_buffer) >= self.history_buffer_flush_interval:
            self._flush_line_buffer()

    def _flush_line_buffer(self) -> None:
        """
        Flushes the line buffer into the log file.
        :return: None
        """

        with open(self.base_module.workspace.ensure_directory("tmp") / (str(self.pid) + ".quickservehistory"), "ab") as f:
            f.writelines(self.lines_buffer)
        self.lines_buffer.clear()

    def _get_terminal_history(self) -> list[bytes]:
        """
        Retrieves the raw, unparsed terminal history from the log file, and the line buffer.
        :return: A list of the lines from the history.
        """

        if self.proc is None:
            return self.lines_buffer

        history_path = self.base_module.workspace.ensure_directory("tmp") / (str(self.pid) + ".quickservehistory")
        if not history_path.exists():
            return self.lines_buffer

        with open(history_path, "rb") as f:
            lines = f.readlines()

        lines.extend(self.lines_buffer)

        return lines

    @staticmethod
    def _parse_line_history(lines: list[bytes]) -> list[Tuple[bytes, bytes]]:
        """
        Parses the line history into something to be sent to the frontend
        :param lines: The raw line history from ManagedProcess._get_terminal_history()
        :return: A list of tuples with (stdio_type, data)
        """

        new_lines = []
        for line in lines:
            stdio_type, line = line.split(b":::", 1)
            new_lines.append((stdio_type, line))
        return new_lines

    def get_terminal_history(self) -> list[Tuple[bytes, bytes]]:
        """
        Gets the terminal history
        :return: A list of tuples with (stdio_type, data)
        """

        raw_history = self._get_terminal_history()
        return self._parse_line_history(raw_history)

    def start(self) -> None:
        """
        Starts the process
        :return: None
        """

        self.proc: Popen = Popen(
            self.command, stdin=PIPE, stderr=PIPE, stdout=PIPE, cwd=self.root_dir
        )
        Thread(target=self._handle_stdout, daemon=True).start()
        Thread(target=self._handle_stderr, daemon=True).start()

    def _handle_stdout(self) -> None:
        """
        Handles stdout from the process.
        :return: None
        """

        assert self.proc is not None
        for line in iter(self.proc.stdout.readline, b""):  # noqa
            for callback in self._on_stdout:
                with self.line_buffer_lock:
                    self.save_stdout(line)
                callback(line)

    def _handle_stderr(self):
        """
        Handles stderr from the process.
        :return: None
        """

        assert self.proc is not None
        for line in iter(self.proc.stderr.readline, b""):  # noqa
            for callback in self._on_stderr:
                with self.line_buffer_lock:
                    self.save_stderr(line)
                callback(line)

    @property
    def pid(self) -> int:
        """
        Returns the processes PID.
        :return: The PID of the process.
        """
        assert self.proc is not None
        return self.proc.pid

    def terminate(self) -> None:
        """
        Sends a SIGTERM signal to the process.
        :return: None
        """

        if not self.is_alive():
            return
        os.kill(self.pid, signal.SIGTERM)

    def kill(self) -> None:
        """
        Sends a SIGKILL signal to the process.
        :return: None
        """

        if not self.is_alive():
            return
        os.kill(self.pid, signal.SIGKILL)

    def is_alive(self) -> bool:
        """
        Checks if the process is still running.
        :return: True if the process is running, else False.
        """
        if self.proc is None:
            return False
        self.proc.poll()
        return self.proc.returncode is None

    def on_stdout(self, callback: Callable[[bytes], None]) -> Callable[[bytes], None]:
        """
        Registers a callback to be called when stdout is received.
        :return: The callback
        """

        self._on_stdout.append(callback)
        return callback

    def on_stderr(self, callback: Callable[[bytes], None]) -> Callable[[bytes], None]:
        """
        Registers a callback to be called when stderr is received.
        :return: The callback
        """

        self._on_stderr.append(callback)
        return callback

    def wait(self) -> int:
        """
        Waits for the process to terminate.
        :return: The process's exit code.
        """

        assert self.proc is not None
        return self.proc.wait()

    def write(self, stdin: bytes) -> int:
        """
        Sends standard input to the process.

        :param stdin: The data to send to the process.
        :return: Number of bytes written, if proc is dead returns -1
        """

        if self.is_alive():
            assert self.proc is not None
            assert self.proc.stdin is not None

            with self.line_buffer_lock:
                self.save_stdin(stdin)
            written = self.proc.stdin.write(stdin)
            self.proc.stdin.flush()
            return written
        return -1
