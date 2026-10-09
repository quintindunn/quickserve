"""
Tests the QuickServeModuleLibrary process backend

Author: Quintin Dunn
Date: 10/09/2026
"""

import signal
from unittest import TestCase
from unittest.mock import MagicMock, patch

from QuickServeModuleLibrary.process import ManagedProcess


class TestManagedProcess(TestCase):
    """Tests for ManagedProcess."""

    def setUp(self):
        """Create a process for testing."""

        self.process = ManagedProcess("test_command")

    def test_init(self):
        """Test process initialization."""

        self.assertEqual(self.process.command, "test_command")
        self.assertIsNone(self.process.proc)
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

        with self.assertRaises(AssertionError):
            _ = self.process.pid

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
