"""Receive framed MessagePack messages through a Waveshare USB-TO-LoRa-HF."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys

import serial
from dotenv import load_dotenv

from protocol import FrameReader, decode_message


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate (default: 115200)")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().with_name(".env"))
    port = os.environ.get("PORT", "").strip()
    if not port:
        parser.error("PORT environment variable is required (e.g. PORT=/dev/ttyACM0)")

    try:
        with serial.Serial(port, args.baud, timeout=1) as radio:
            print(f"listening on {port} at {args.baud} baud. Press Ctrl-C to stop.", flush=True)
            reader = FrameReader()
            while True:
                for frame in reader.feed(radio.read(min(radio.in_waiting or 1, 256))):
                    try:
                        timestamp, message = decode_message(frame)
                        added = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S")
                    except (ValueError, OverflowError, OSError) as error:
                        print(f"Discarded invalid message: {error}", file=sys.stderr, flush=True)
                        continue
                    print(f"[{added}] Received: {json.dumps(message)}", flush=True)
    except KeyboardInterrupt:
        return 0
    except (serial.SerialException, OSError, ValueError) as error:
        print(f"receiver error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
