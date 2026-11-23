"""Regression tests for the Waveshare AT entry handshake; no hardware needed."""

from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

import set_at


class ATTests(unittest.TestCase):
    def exchange(self, command, response, **kwargs):
        radio = MagicMock()
        chunks = iter([response])
        radio.read.side_effect = lambda size: next(chunks, b"")
        ticks = (n / 10 for n in range(1000))
        with patch.object(set_at.time, "monotonic", side_effect=ticks), redirect_stdout(io.StringIO()):
            return set_at.exchange(radio, command, **kwargs)

    def test_entry_echo_is_accepted(self):
        self.assertEqual(self.exchange("+++", b"+++\r\n"), "+++")

    def test_silent_entry_still_fails(self):
        with self.assertRaises(RuntimeError):
            self.exchange("+++", b"")

    def test_echo_only_version_or_setter_fails(self):
        for command in ("AT+VER", "AT+SF=10"):
            with self.subTest(command=command), self.assertRaises(RuntimeError):
                self.exchange(command, (command + "\r\n").encode())

    def test_acknowledged_setter_passes(self):
        self.exchange("AT+SF=10", b"AT+SF=10\r\nOK\r\n", require_ok=True)

    def test_setter_waits_for_delayed_ack_after_echo(self):
        radio = MagicMock()
        elapsed = 0

        def read(size):
            nonlocal elapsed
            elapsed += 0.1
            if elapsed < 0.15:
                return b"AT+SF=10\r\n"
            if elapsed >= 1.2:
                return b"OK\r\n"
            return b""

        radio.read.side_effect = read
        with patch.object(set_at.time, "monotonic", side_effect=lambda: elapsed), redirect_stdout(io.StringIO()):
            response = set_at.exchange(radio, "AT+SF=10", require_ok=True)
        self.assertIn("OK", response)
        self.assertGreaterEqual(elapsed, 1.2)

    def test_timeout_diagnostics(self):
        for response, reason in ((b"", "Timed out"), (b"AT+SF=10\r\n", "Only an echo"),
                                 (b"ERROR\r\n", "Dongle reported an error")):
            with self.subTest(reason=reason), self.assertRaisesRegex(RuntimeError, reason):
                self.exchange("AT+SF=10", response, require_ok=True)

    def test_error_still_fails(self):
        with self.assertRaises(RuntimeError):
            self.exchange("+++", b"+++\r\nERROR\r\n")

    def test_file_requires_version_before_settings(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "commands.at"
            path.write_text("+++\nAT+SF=10\nAT+EXIT\n")
            with self.assertRaisesRegex(ValueError, "AT\\+VER must immediately follow"):
                set_at.read_commands(path)
        set_at.read_commands(Path(set_at.__file__).with_name("commands.at"))

    def run_session(self, version_response, mismatch=False):
        radio = MagicMock()
        chunks = iter([])
        seen = []
        values = {name: bounds[0] for name, bounds in set_at.RANGES.items()}

        def write(payload):
            nonlocal chunks
            seen.append(payload.decode().strip())
            reply = {
                "+++": b"+++\r\n",
                "AT+VER": version_response,
                "AT+EXIT": b"EXIT\r\nOK\r\n",
            }.get(seen[-1], b"OK\r\n")
            if "=" in seen[-1]:
                name, value = seen[-1][3:].split("=", 1)
                values[name] = int(value)
            if seen[-1].endswith("?"):
                name = seen[-1][3:-1]
                value = values[name]
                if mismatch and name == "TXCH" and "AT+TXCH=65" in seen:
                    value = 18
                reply = f"+{name}:{value}\r\nOK\r\n".encode()
            chunks = iter([reply])

        radio.write.side_effect = write
        radio.read.side_effect = lambda size: next(chunks, b"")
        opened = MagicMock()
        opened.__enter__.return_value = radio
        ticks = (n / 10 for n in range(10000))
        with patch.dict(os.environ, {"PORT": "/dev/test"}), patch.object(set_at, "load_dotenv"), patch("sys.argv", ["set_at.py"]), patch.object(set_at.serial, "Serial", return_value=opened), patch.object(set_at.time, "monotonic", side_effect=ticks), patch.object(set_at.time, "sleep"), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = set_at.main()
        return result, seen

    def test_full_session_with_echo_only_entry(self):
        result, seen = self.run_session(b"AT+VER\r\nVER: test\r\nOK\r\n")
        self.assertEqual(result, 0)
        self.assertEqual(seen, set_at.read_commands(Path(set_at.__file__).with_name("commands.at")))

    def test_failed_version_sends_no_settings_and_exits(self):
        result, seen = self.run_session(b"AT+VER\r\n")
        self.assertEqual(result, 1)
        self.assertEqual(seen, ["+++", "AT+VER", "AT+EXIT"])

    def test_readback_formats(self):
        for response in ("AT+SF?\n10\nOK", "+SF:10\nOK", "SF=10\nOK"):
            self.assertEqual(set_at.readback_value("AT+SF?", response), 10)
        for response in ("AT+SF?\nOK", "OK", "garbage\nOK", "10\n11\nOK"):
            with self.assertRaises(RuntimeError):
                set_at.readback_value("AT+SF?", response)

    def test_readback_mismatch_stops_and_exits(self):
        result, seen = self.run_session(b"Ver1.2\r\nOK\r\n", mismatch=True)
        self.assertEqual(result, 1)
        self.assertEqual(seen[-3:], ["AT+TXCH=65", "AT+TXCH?", "AT+EXIT"])
        self.assertNotIn("AT+RXCH=65", seen)


if __name__ == "__main__":
    unittest.main()
