"""Listen for newline-delimited messages through a Waveshare USB-TO-LoRa-HF."""

import argparse
import os
from pathlib import Path
import sys

import serial
from dotenv import load_dotenv


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
            pending = bytearray()
            while True:
                pending.extend(radio.read_until(b"\n"))
                if pending.endswith(b"\n"):
                    print(pending.decode("utf-8", errors="replace").rstrip("\r\n"), flush=True)
                    pending.clear()
    except KeyboardInterrupt:
        return 0
    except (serial.SerialException, OSError, ValueError) as error:
        print(f"receiver error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
