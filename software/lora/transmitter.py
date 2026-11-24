"""Send a sample location payload with a fresh random UUID over LoRa."""

import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path
import sys
import time
from uuid import uuid4

import serial
from dotenv import load_dotenv

from protocol import encode_message

LOCATION_PAYLOAD = {
    "date": "2026-11-20",
    "time": "00:54:57",
    "altitude_m": 126.7,
    "vertical_speed_mpm": 0.2,
    "speed_kn": 0.0,
    "course_d": 0.0,
    "direction": "N",
    "added": "2026-11-19T18:54:57.893046-06:00",
    "latitude": 00.20332,
    "longitude": 00.21067,
    "_meta": {"channel": "location"},
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate (default: 115200)")
    parser.add_argument("--interval", type=float, default=5, help="Seconds between messages (default: 5)")
    parser.add_argument("--once", action="store_true", help="Send one message and exit")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().with_name(".env"))
    port = os.environ.get("PORT", "").strip()
    if not port:
        parser.error("PORT environment variable is required (e.g. PORT=/dev/ttyACM0)")
    if not math.isfinite(args.interval) or args.interval <= 0:
        parser.error("--interval must be a positive, finite number")

    try:
        with serial.Serial(port, args.baud, write_timeout=5) as radio:
            print(f"transmitting on {port} at {args.baud} baud. Press Ctrl-C to stop.", flush=True)
            while True:
                now = datetime.now()
                timestamp = int(now.timestamp())
                payload = {"id": str(uuid4()), **LOCATION_PAYLOAD}
                radio.write(encode_message(payload, timestamp))
                radio.flush()
                print(f"[{now:%Y-%m-%dT%H:%M:%S}] (sent) {json.dumps(payload)}", flush=True)
                if args.once:
                    return 0
                time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0
    except (serial.SerialException, OSError, ValueError) as error:
        print(f"transmitter error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
