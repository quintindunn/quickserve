"""
Tests the QuickServeModuleLibrary process backend

Author: Quintin Dunn
Date: 10/09/2026
"""

import signal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch, Mock

from QuickServeModuleLibrary.process import ManagedProcess


class TestManagedProcess(TestCase):
    """Tests for ManagedProcess."""

    def setUp(self):
        """Create a process for testing."""

        self.temp_dir = TemporaryDirectory()
        (Path(self.temp_dir.name) / "tmp").mkdir()
        self.workspace = MagicMock()
        self.workspace.ensure_directory.side_effect = (
            lambda directory: Path(self.temp_dir.name) / directory
        )

        self.base_module = MagicMock()
        self.base_module.workspace = self.workspace

        self.process = ManagedProcess("test_command", self.base_module)
        self.process.proc = Mock(pid=1234)

    def tearDown(self):
        """Clean up temporary files."""

        self.temp_dir.cleanup()

    def test_init(self):
        """Test process initialization."""

        self.assertEqual(self.process.command, "test_command")
        self.assertIsNone(self.process.root_dir)

    def test_start(self):
        """Test starting a process."""

        with (
            patch("QuickServeModuleLibrary.process.Popen") as mock_popen,
            patch("QuickServeModuleLibrary.process.Thread") as mock_thread,
        ):
            self.process.start()

        mock_popen.assert_called_once_with(
            "test_command",
            stdin=-1,
            stderr=-1,
            stdout=-1,
            cwd=None,
        )
        self.assertEqual(mock_thread.call_count, 2)

    def test_pid(self):
        """Test retrieving the process PID."""

        self.process.proc = MagicMock()
        self.process.proc.pid = 1234

        self.assertEqual(self.process.pid, 1234)

    def test_terminate_and_kill(self):
        """Test sending termination and kill signals."""

        self.process.proc = MagicMock()
        self.process.proc.pid = 1234
        self.process.proc.returncode = None

        with patch("QuickServeModuleLibrary.process.os.kill") as mock_kill:
            self.process.terminate()
            mock_kill.assert_called_with(1234, signal.SIGTERM)

            self.process.kill()
            mock_kill.assert_called_with(1234, signal.SIGKILL)

            self.assertEqual(mock_kill.call_count, 2)

    def test_is_alive(self):
        """Test checking whether the process is running."""

        self.assertFalse(self.process.is_alive())

        self.process.proc = MagicMock()
        self.process.proc.returncode = None
        self.assertTrue(self.process.is_alive())

        self.process.proc.returncode = 0
        self.assertFalse(self.process.is_alive())

    def test_stdout_callback(self):
        """Test receiving process stdout."""

        callback = MagicMock()

        self.assertIs(self.process.on_stdout(callback), callback)
        self.process.proc = MagicMock()
        self.process.proc.stdout.readline.side_effect = [b"foo\n", b""]  # noqa

        self.process._handle_stdout()

        callback.assert_called_once_with(b"foo\n")

    def test_stderr_callback(self):
        """Test receiving process stderr."""

        callback = MagicMock()

        self.assertIs(self.process.on_stderr(callback), callback)
        self.process.proc = MagicMock()
        self.process.proc.stderr.readline.side_effect = [b"error\n", b""]  # noqa

        self.process._handle_stderr()

        callback.assert_called_once_with(b"error\n")

    def test_write(self):
        """Test writing to process stdin."""

        self.process.proc = MagicMock()
        self.process.proc.returncode = None
        self.process.proc.stdin.write.return_value = 5  # noqa

        self.assertEqual(self.process.write(b"foo"), 5)
        self.process.proc.stdin.write.assert_called_once_with(b"foo")  # noqa
        self.process.proc.stdin.flush.assert_called_once()  # noqa

    def test_write_when_not_alive(self):
        """Test writing when the process is not running."""

        self.assertEqual(self.process.write(b"foo"), -1)

        self.process.proc = MagicMock()
        self.process.proc.returncode = 1

        self.assertEqual(self.process.write(b"foo"), -1)
        self.process.proc.stdin.write.assert_not_called()  # noqa

    def test_save_stdio(self):
        """Tests saving stdio to terminal history"""

        self.process._save_stdio(b"stdin", b"input\n")

        self.assertEqual(
            self.process.lines_buffer,
            [b"stdin:::input\n"],
        )

    def test_save_stdio_flushes_at_interval(self):
        """Tests that the process history buffer flushes at the right time"""

        self.process.history_buffer_flush_interval = 2

        with patch.object(self.process, "_flush_line_buffer") as mock_flush:
            self.process.save_stdout(b"first\n")
            mock_flush.assert_not_called()

            self.process.save_stderr(b"second\n")
            mock_flush.assert_called_once()

    def test_flush_line_buffer(self):
        """Tests that the line buffer flushes properly"""

        self.process.lines_buffer = [
            b"stdout:::hello\n",
            b"stderr:::error\n",
        ]

        self.process._flush_line_buffer()

        history_path = (
            self.workspace.ensure_directory("tmp")
            / f"{self.process.pid}.quickservehistory"
        )

        with open(history_path, "rb") as f:
            self.assertEqual(
                f.readlines(),
                [b"stdout:::hello\n", b"stderr:::error\n"],
            )

        self.assertEqual(self.process.lines_buffer, [])
        self.assertTrue(self.process.line_buffer_has_written)

    def test_flush_line_buffer_removes_existing_history(self):
        """Tests that old files that happen to have the same PID get overwritten"""

        history_dir = self.workspace.ensure_directory("tmp")
        history_path = history_dir / f"{self.process.pid}.quickservehistory"
        history_path.write_bytes(b"old history\n")

        self.process.lines_buffer = [b"stdout:::new history\n"]
        self.process._flush_line_buffer()

        self.assertEqual(
            history_path.read_bytes(),
            b"stdout:::new history\n",
        )

    def test_flush_line_buffer_appends_after_first_flush(self):
        """Tests that the file isn't overwriting existing data it shouldn't."""

        self.process.lines_buffer = [b"stdout:::first\n"]
        self.process._flush_line_buffer()

        self.process.lines_buffer = [b"stdout:::second\n"]
        self.process._flush_line_buffer()

        history_path = (
            self.workspace.ensure_directory("tmp")
            / f"{self.process.pid}.quickservehistory"
        )

        self.assertEqual(
            history_path.read_bytes(),
            b"stdout:::first\nstdout:::second\n",
        )

    def test_get_terminal_history_combines_file_and_buffer(self):
        """Tests that get_terminal_history combines the buffer and history file."""

        self.process.lines_buffer = [b"stderr:::buffered\n"]

        self.process._flush_line_buffer()
        self.process.lines_buffer = [b"stdout:::pending\n"]
        self.process.proc = Mock(pid=self.process.pid)

        self.assertEqual(
            self.process._get_terminal_history(),
            [
                b"stderr:::buffered\n",
                b"stdout:::pending\n",
            ],
        )

    def test_parse_line_history(self):
        """Tests parsing individual lines from the history file/buffer parses properly"""

        lines = [
            b"stdout:::hello\n",
            b"stderr:::error\n",
            b"stdin:::input\n",
            b"stdin:::foo:::bar\n"
        ]

        self.assertEqual(
            ManagedProcess._parse_line_history(lines),
            [
                (b"stdout", b"hello\n"),
                (b"stderr", b"error\n"),
                (b"stdin", b"input\n"),
            ],
        )

    def test_parse_line_history_preserves_separator_in_data(self):
        """Tests that the line doesn't accidentally split on the wrong part when parsing."""

        lines = [b"stdout:::value:::continued\n"]

        self.assertEqual(
            ManagedProcess._parse_line_history(lines),
            [(b"stdout", b"value:::continued\n")],
        )

    def test_get_terminal_history(self):
        """Tests getting the terminal history"""

        self.process.lines_buffer = [
            b"stdout:::hello\n",
            b"stderr:::error\n",
        ]

        self.assertEqual(
            self.process.get_terminal_history(),
            [
                (b"stdout", b"hello\n"),
                (b"stderr", b"error\n"),
            ],
        )