"""Versioned MessagePack messages with bounded COBS framing and CRC32."""

import math
import struct
import zlib

from cobs import cobs
import msgpack

VERSION = 3
# Bound memory while allowing messages larger than one 240-byte radio packet.
# The dongle handles radio packetization in transparent stream mode.
MAX_WIRE_BYTES = 768
MAX_FRAME_BYTES = MAX_WIRE_BYTES - 2
MAX_NESTING = 16


def validate_json(value, depth=0):
    """Check JSON-compatible types and resource bounds, not application fields."""
    if depth > MAX_NESTING:
        raise ValueError("JSON payload exceeds nesting limit")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if not -(2**63) <= value < 2**64:
            raise ValueError("Integer is outside MessagePack's 64-bit range")
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_FRAME_BYTES:
            raise ValueError("JSON string exceeds frame size limit")
        return
    if isinstance(value, (dict, list)):
        if len(value) > MAX_FRAME_BYTES:
            raise ValueError("JSON container exceeds frame size limit")
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ValueError("JSON object keys must be strings")
                validate_json(key, depth + 1)
                validate_json(item, depth + 1)
        else:
            for item in value:
                validate_json(item, depth + 1)
        return
    raise ValueError("Payload must contain JSON-compatible values")


def validate(message):
    if not isinstance(message, list) or len(message) != 3:
        raise ValueError("Expected [version, Unix timestamp, payload]")
    version, timestamp, payload = message
    if type(version) is not int or version != VERSION:
        raise ValueError("Unsupported message version")
    if type(timestamp) is not int or not 0 <= timestamp <= 253402300799:
        raise ValueError("Invalid Unix timestamp")
    validate_json(payload)
    return timestamp, payload


def encode_message(payload, timestamp: int) -> bytes:
    message = [VERSION, timestamp, payload]
    validate(message)
    packed = msgpack.packb(message, use_bin_type=True)
    checksum = struct.pack(">I", zlib.crc32(packed))
    frame = cobs.encode(packed + checksum)
    if len(frame) > MAX_FRAME_BYTES:
        raise ValueError(f"Encoded message exceeds the {MAX_WIRE_BYTES}-byte wire limit")
    return b"\x00" + frame + b"\x00"


def decode_message(frame: bytes) -> tuple[int, object]:
    """Decode one COBS frame, without its delimiters."""
    if not frame or len(frame) > MAX_FRAME_BYTES:
        raise ValueError("Empty or oversized frame")
    try:
        data = cobs.decode(frame)
    except cobs.DecodeError as error:
        raise ValueError("Invalid COBS frame") from error
    if len(data) < 5:
        raise ValueError("Truncated frame")
    payload, checksum = data[:-4], data[-4:]
    if struct.unpack(">I", checksum)[0] != zlib.crc32(payload):
        raise ValueError("CRC32 mismatch")
    try:
        message = msgpack.unpackb(payload, raw=False, max_str_len=MAX_FRAME_BYTES,
                                  max_bin_len=0, max_array_len=MAX_FRAME_BYTES, max_map_len=MAX_FRAME_BYTES,
                                  max_ext_len=0)
    except (ValueError, TypeError, msgpack.UnpackException) as error:
        raise ValueError("Invalid MessagePack payload") from error
    return validate(message)


class FrameReader:
    """Retain fragments across reads and resynchronize at zero delimiters."""

    def __init__(self):
        self.pending = bytearray()
        self.discarding = False

    def feed(self, chunk: bytes):
        for value in chunk:
            if value == 0:
                if self.pending and not self.discarding:
                    yield bytes(self.pending)
                self.pending.clear()
                self.discarding = False
            elif not self.discarding:
                if len(self.pending) == MAX_FRAME_BYTES:
                    self.pending.clear()
                    self.discarding = True
                else:
                    self.pending.append(value)
