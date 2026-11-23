"""Versioned MessagePack messages with bounded COBS framing and CRC32."""

import struct
import zlib

from cobs import cobs
import msgpack

VERSION = 1
# Include both zero delimiters inside the dongle's documented 240-byte packet size.
MAX_FRAME_BYTES = 238
MAX_TEXT_BYTES = 200


def validate(message):
    if not isinstance(message, list) or len(message) != 3:
        raise ValueError("Expected [version, Unix timestamp, message]")
    version, timestamp, text = message
    if type(version) is not int or version != VERSION:
        raise ValueError("Unsupported message version")
    if type(timestamp) is not int or not 0 <= timestamp <= 253402300799:
        raise ValueError("Invalid Unix timestamp")
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise ValueError("Invalid or oversized message text")
    return timestamp, text


def encode_message(text: str, timestamp: int) -> bytes:
    message = [VERSION, timestamp, text]
    validate(message)
    payload = msgpack.packb(message, use_bin_type=True)
    checksum = struct.pack(">I", zlib.crc32(payload))
    frame = cobs.encode(payload + checksum)
    if len(frame) > MAX_FRAME_BYTES:
        raise ValueError("Encoded message exceeds the 240-byte wire limit")
    # A leading delimiter also separates this frame from a lost trailing delimiter.
    return b"\x00" + frame + b"\x00"


def decode_message(frame: bytes) -> tuple[int, str]:
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
        message = msgpack.unpackb(payload, raw=False, max_str_len=MAX_TEXT_BYTES,
                                  max_bin_len=0, max_array_len=3, max_map_len=0,
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
