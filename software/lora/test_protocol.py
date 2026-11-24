"""Binary protocol regression tests; no radio hardware needed."""

from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
import io
import os
import struct
import unittest
from unittest.mock import MagicMock, patch
from uuid import UUID
import zlib

from cobs import cobs
import msgpack

from protocol import FrameReader, MAX_FRAME_BYTES, decode_message, encode_message
import receiver
import transmitter

TIMESTAMP = 1795457109
LOCATION = {"id": "3e9d33a2-efe3-46a8-94c8-e85237f2932d", **transmitter.LOCATION_PAYLOAD}


class ProtocolTests(unittest.TestCase):
    def test_round_trip_and_size(self):
        wire = encode_message(LOCATION, TIMESTAMP)
        self.assertEqual(len(wire), 283)
        self.assertEqual(wire[:1], b"\x00")
        self.assertEqual(wire[-1:], b"\x00")
        self.assertNotIn(0, wire[1:-1])
        self.assertEqual(decode_message(wire[1:-1]), (TIMESTAMP, LOCATION))

    def test_varying_json_payloads(self):
        payloads = [
            {}, {"percent": 75, "temperature_c": 20.5},
            {"new_field": [None, True, False, {"text": "café 🎈\x00\n"}]},
            [1, "text", None], "hello", None, False, 123, -1.5,
            {"id": "not-a-uuid", "latitude": "not-location-data", "_meta": {"channel": "other"}},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                wire = encode_message(payload, TIMESTAMP)
                self.assertEqual(decode_message(wire[1:-1]), (TIMESTAMP, payload))

    def test_every_split_and_multiple_frames(self):
        wire = encode_message(LOCATION, TIMESTAMP)
        for split in range(len(wire) + 1):
            reader = FrameReader()
            frames = list(reader.feed(wire[:split])) + list(reader.feed(wire[split:]))
            self.assertEqual(len(frames), 1)
            self.assertEqual(decode_message(frames[0]), (TIMESTAMP, LOCATION))
        self.assertEqual(len(list(FrameReader().feed(wire * 3))), 3)

    def test_corruption_is_rejected_then_recovers(self):
        wire = encode_message(LOCATION, TIMESTAMP)
        data = bytearray(cobs.decode(wire[1:-1]))
        data[-1] ^= 1
        damaged = cobs.encode(bytes(data))
        with self.assertRaisesRegex(ValueError, "CRC32"):
            decode_message(damaged)
        frames = list(FrameReader().feed(b"\x00" + damaged + b"\x00" + wire))
        self.assertEqual(decode_message(frames[-1]), (TIMESTAMP, LOCATION))
        for invalid in (b"", b"\x05ab", cobs.encode(b"abc")):
            with self.assertRaises(ValueError):
                decode_message(invalid)

    def test_start_midstream_and_missing_delimiter(self):
        wire = encode_message(LOCATION, TIMESTAMP)
        frames = list(FrameReader().feed(wire[8:] + wire))
        self.assertEqual(decode_message(frames[-1]), (TIMESTAMP, LOCATION))
        frames = list(FrameReader().feed(wire[:-1] + wire))
        self.assertEqual(len(frames), 2)

    def test_bounds_and_oversize_resynchronization(self):
        with self.assertRaises(ValueError):
            encode_message({"text": "x" * 1000}, TIMESTAMP)
        with self.assertRaisesRegex(ValueError, "768-byte"):
            encode_message({"a": "x" * 400, "b": "x" * 400}, TIMESTAMP)
        wire = encode_message(LOCATION, TIMESTAMP)
        self.assertGreater(len(wire), 240)
        self.assertLessEqual(len(wire), 768)
        reader = FrameReader()
        self.assertEqual(list(reader.feed(b"x" * 10000)), [])
        self.assertLessEqual(len(reader.pending), MAX_FRAME_BYTES)
        frames = list(reader.feed(wire))
        self.assertEqual(len(frames), 1)
        self.assertEqual(decode_message(frames[0]), (TIMESTAMP, LOCATION))

    def test_invalid_envelopes_and_non_json_types(self):
        nested = None
        for _ in range(20):
            nested = [nested]
        cases = ([2, TIMESTAMP, {}], [3, True, {}], [True, TIMESTAMP, {}],
                 [3, -1, {}], [3, TIMESTAMP], {},
                 [3, TIMESTAMP, {1: "non-string key"}], [3, TIMESTAMP, b"binary"],
                 [3, TIMESTAMP, float("nan")], [3, TIMESTAMP, float("inf")],
                 [3, TIMESTAMP, nested])
        for message in cases:
            packed = msgpack.packb(message, use_bin_type=True)
            frame = cobs.encode(packed + struct.pack(">I", zlib.crc32(packed)))
            with self.subTest(message=message), self.assertRaises(ValueError):
                decode_message(frame)
        for payload in ({1: "key"}, b"bytes", (1, 2), float("inf"), 2**64, nested):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                encode_message(payload, TIMESTAMP)

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
        timestamp, sent_payload = decode_message(wire[1:-1])
        self.assertEqual(timestamp, TIMESTAMP)
        self.assertEqual(UUID(sent_payload["id"]).version, 4)
        self.assertEqual({key: value for key, value in sent_payload.items() if key != "id"}, transmitter.LOCATION_PAYLOAD)
        radio.in_waiting = 0
        radio.read.side_effect = [b"\x00\x05ab\x00", wire[:8], wire[8:], KeyboardInterrupt]
        with patch.dict(os.environ, {"PORT": "/dev/test"}), patch("sys.argv", ["receiver.py"]), patch.object(receiver, "load_dotenv"), patch.object(receiver.serial, "Serial", return_value=opened), redirect_stdout(output), redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(receiver.main(), 0)
        self.assertIn(f"[{now:%Y-%m-%dT%H:%M:%S}] (sent)", output.getvalue())
        self.assertIn(f"[{now:%Y-%m-%dT%H:%M:%S}] (received)", output.getvalue())
        import json
        received_line = next(line for line in output.getvalue().splitlines() if "] (received) " in line)
        self.assertEqual(json.loads(received_line.split("] (received) ", 1)[1]), sent_payload)
        self.assertIn("Discarded invalid message", errors.getvalue())

    def test_fresh_random_uuid_for_each_send(self):
        opened = MagicMock()
        radio = opened.__enter__.return_value
        with patch.dict(os.environ, {"PORT": "/dev/test"}), patch("sys.argv", ["transmitter.py"]), patch.object(transmitter, "load_dotenv"), patch.object(transmitter.serial, "Serial", return_value=opened), patch.object(transmitter.time, "sleep", side_effect=[None, KeyboardInterrupt]), redirect_stdout(io.StringIO()):
            self.assertEqual(transmitter.main(), 0)
        payloads = [decode_message(call.args[0][1:-1])[1] for call in radio.write.call_args_list]
        self.assertEqual(len(payloads), 2)
        self.assertNotEqual(payloads[0]["id"], payloads[1]["id"])
        self.assertTrue(all(UUID(payload["id"]).version == 4 for payload in payloads))
        self.assertNotIn("id", transmitter.LOCATION_PAYLOAD)


if __name__ == "__main__":
    unittest.main()
