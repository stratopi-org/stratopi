"""Binary protocol regression tests; no radio hardware needed."""

from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
import io
import os
import struct
import unittest
from unittest.mock import MagicMock, patch
import zlib

from cobs import cobs
import msgpack

from protocol import FrameReader, MAX_FRAME_BYTES, decode_message, encode_message
import receiver
import transmitter

TIMESTAMP = 1795457109


class ProtocolTests(unittest.TestCase):
    def test_round_trip_and_size(self):
        wire = encode_message("hello world", TIMESTAMP)
        self.assertEqual(len(wire), 26)
        self.assertEqual(wire[:1], b"\x00")
        self.assertEqual(wire[-1:], b"\x00")
        self.assertNotIn(0, wire[1:-1])
        self.assertEqual(decode_message(wire[1:-1]), (TIMESTAMP, "hello world"))

    def test_binary_characters_and_unicode(self):
        for text in ("", "hello\x00\nworld", "café 🎈"):
            wire = encode_message(text, TIMESTAMP)
            self.assertEqual(decode_message(wire[1:-1]), (TIMESTAMP, text))

    def test_every_split_and_multiple_frames(self):
        wire = encode_message("hello world", TIMESTAMP)
        for split in range(len(wire) + 1):
            reader = FrameReader()
            frames = list(reader.feed(wire[:split])) + list(reader.feed(wire[split:]))
            self.assertEqual(len(frames), 1)
            self.assertEqual(decode_message(frames[0]), (TIMESTAMP, "hello world"))
        self.assertEqual(len(list(FrameReader().feed(wire * 3))), 3)

    def test_corruption_is_rejected_then_recovers(self):
        wire = encode_message("hello world", TIMESTAMP)
        data = bytearray(cobs.decode(wire[1:-1]))
        data[-1] ^= 1
        damaged = cobs.encode(bytes(data))
        with self.assertRaisesRegex(ValueError, "CRC32"):
            decode_message(damaged)
        frames = list(FrameReader().feed(b"\x00" + damaged + b"\x00" + wire))
        self.assertEqual(decode_message(frames[-1]), (TIMESTAMP, "hello world"))
        for invalid in (b"", b"\x05ab", cobs.encode(b"abc")):
            with self.assertRaises(ValueError):
                decode_message(invalid)

    def test_start_midstream_and_missing_delimiter(self):
        wire = encode_message("hello world", TIMESTAMP)
        frames = list(FrameReader().feed(wire[8:] + wire))
        self.assertEqual(decode_message(frames[-1]), (TIMESTAMP, "hello world"))
        frames = list(FrameReader().feed(wire[:-1] + wire))
        self.assertEqual(len(frames), 2)

    def test_bounds_and_oversize_resynchronization(self):
        with self.assertRaises(ValueError):
            encode_message("é" * 101, TIMESTAMP)
        wire = encode_message("x" * 200, TIMESTAMP)
        self.assertLessEqual(len(wire), 240)
        reader = FrameReader()
        self.assertEqual(list(reader.feed(b"x" * 10000)), [])
        self.assertLessEqual(len(reader.pending), MAX_FRAME_BYTES)
        frames = list(reader.feed(wire))
        self.assertEqual(len(frames), 1)
        self.assertEqual(decode_message(frames[0]), (TIMESTAMP, "x" * 200))

    def test_invalid_schemas_with_valid_crc(self):
        for message in ([2, TIMESTAMP, "x"], [1, True, "x"], [True, TIMESTAMP, "x"],
                        [1, -1, "x"], [1, TIMESTAMP, 3], [1, TIMESTAMP], {}):
            payload = msgpack.packb(message, use_bin_type=True)
            frame = cobs.encode(payload + struct.pack(">I", zlib.crc32(payload)))
            with self.subTest(message=message), self.assertRaises(ValueError):
                decode_message(frame)

    def test_apps_use_binary_and_display_formatted_timestamp(self):
        radio = MagicMock()
        opened = MagicMock()
        opened.__enter__.return_value = radio
        now = datetime.fromtimestamp(TIMESTAMP)
        output = io.StringIO()
        with patch.dict(os.environ, {"PORT": "/dev/test"}), patch("sys.argv", ["transmitter.py", "--once"]), patch.object(transmitter, "load_dotenv"), patch.object(transmitter.serial, "Serial", return_value=opened), patch.object(transmitter, "datetime") as clock, redirect_stdout(output):
            clock.now.return_value = now
            self.assertEqual(transmitter.main(), 0)
        wire = radio.write.call_args.args[0]
        self.assertEqual(decode_message(wire[1:-1]), (TIMESTAMP, "hello world"))
        radio.in_waiting = 0
        radio.read.side_effect = [b"\x00\x05ab\x00", wire[:8], wire[8:], KeyboardInterrupt]
        with patch.dict(os.environ, {"PORT": "/dev/test"}), patch("sys.argv", ["receiver.py"]), patch.object(receiver, "load_dotenv"), patch.object(receiver.serial, "Serial", return_value=opened), redirect_stdout(output), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(receiver.main(), 0)
        self.assertIn(f"hello world {now:%Y-%m-%dT%H:%M:%S}", output.getvalue())
        self.assertIn("Discarded invalid message", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
