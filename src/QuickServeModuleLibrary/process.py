from pathlib import Path
from subprocess import Popen, PIPE
from typing import Callable

from threading import Thread

import signal
import os


class ManagedProcess:
    proc: Popen | None
    _on_stdout: list[Callable[[bytes], None]]
    _on_stderr: list[Callable[[bytes], None]]
    command: str
    root_dir: Path

    def __init__(self, command, root_dir: Path = None):
        self.command = command
        self.proc = None
        self._on_stderr = list()
        self._on_stdout = list()
        self.root_dir = root_dir

    def start(self):
        self.proc: Popen = Popen(
            self.command, stdin=PIPE, stderr=PIPE, stdout=PIPE, cwd=self.root_dir
        )
        Thread(target=self._handle_stdout, daemon=True).start()
        Thread(target=self._handle_stderr, daemon=True).start()

    def _handle_stdout(self):
        for line in iter(self.proc.stdout.readline, b""):
            for callback in self._on_stdout:
                callback(line)

    def _handle_stderr(self):
        for line in iter(self.proc.stderr.readline, b""):
            for callback in self._on_stderr:
                callback(line)

    @property
    def pid(self) -> int:
        """
        Returns the processes PID.
        :return: The PID of the process.
        """

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

        return self.proc.wait()

    def write(self, stdin: bytes) -> int:
        """
        Sends standard input to the process.

        :param stdin: The data to send to the process.
        :return: Number of bytes written, if proc is dead returns -1
        """

        if self.is_alive():
            written = self.proc.stdin.write(stdin)
            self.proc.stdin.flush()
            return written
        return -1


if __name__ == "__main__":
    process = ManagedProcess(
        [
            "python",
            "-u",
            "-c",
            """
    import sys
    import time

    time.sleep(1)

    print("Hello from stdout!", flush=True)
    print("Hello from stderr!", file=sys.stderr, flush=True)

    for line in sys.stdin:
        line = line.strip()

        if line == "quit":
            break

        print(f"Received: {line}", flush=True)
        
    print("exiting")
    """,
        ]
    )

    @process.on_stdout
    def stdout(data: bytes):
        print(f"[STDOUT] {data.decode().strip()}")

    @process.on_stderr
    def stderr(data: bytes):
        print(f"[STDERR] {data.decode().strip()}")

    process.start()
    print(f"Started process with PID {process.pid}")

    process.write(b"Hello!\n")
    process.write(b"Testing input\n")

    import time

    time.sleep(2)

    process.write(b"quit\n")

    exit_code = process.wait()

    print(f"Process exited with {exit_code}")
