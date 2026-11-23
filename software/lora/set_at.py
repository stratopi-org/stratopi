"""Inspect or configure a Waveshare USB-TO-LoRa-HF using AT commands."""

import argparse
import os
from pathlib import Path
import re
import sys
import time

from dotenv import load_dotenv
import serial

# Only radio settings are accepted here; keep the USB interface usable by the apps.
RANGES = {
    "SF": (7, 12), "BW": (0, 2), "CR": (1, 4), "PWR": (10, 22),
    "NETID": (0, 255), "LBT": (0, 1), "MODE": (1, 3),
    "TXCH": (0, 80), "RXCH": (0, 80), "RSSI": (0, 1), "ADDR": (0, 65535),
}


def read_commands(path: Path) -> list[str]:
    """Validate the entire file before opening the serial port."""
    commands = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        command = raw.split("#", 1)[0].strip()
        if not command:
            continue
        valid = command in {"+++", "AT+VER", "AT+HELP", "AT+EXIT"}
        match = re.fullmatch(r"AT\+([A-Z]+)=(\d+)", command)
        if match and match[1] in RANGES:
            low, high = RANGES[match[1]]
            valid = low <= int(match[2]) <= high
        query = re.fullmatch(r"AT\+([A-Z]+)\?", command)
        if query and query[1] in RANGES:
            valid = True
        if not valid:
            raise ValueError(f"{path.name}:{number}: unsupported command or value: {command}")
        commands.append(command)
    if not commands or commands[0] != "+++" or commands[-1] != "AT+EXIT":
        raise ValueError("commands.at must start with +++ and end with AT+EXIT")
    if commands.count("+++") != 1 or commands.count("AT+EXIT") != 1:
        raise ValueError("Use exactly one +++ and one AT+EXIT in commands.at")
    if len(commands) < 3:
        raise ValueError("commands.at must contain at least one AT command between entry and exit")
    return commands


def exchange(radio, command: str, *, require_ok: bool = False) -> str:
    """Read through a quiet period, bounded by a five-second overall deadline."""
    radio.reset_input_buffer()
    print(f"> {command}", flush=True)
    radio.write((command + "\r\n").encode("ascii"))
    radio.flush()
    response = bytearray()
    deadline = time.monotonic() + 5
    last_data = None
    while time.monotonic() < deadline:
        chunk = radio.read(radio.in_waiting or 1)
        if chunk:
            response.extend(chunk)
            last_data = time.monotonic()
        elif last_data is not None and time.monotonic() - last_data >= 0.5:
            break
    text = response.decode("utf-8", errors="replace").strip()
    print(text or "(no response)", flush=True)
    lines = [line.strip() for line in text.splitlines() if line.strip() != command]
    if not lines or re.search(r"\b(?:ERROR|ERR|FAIL|FAILED)\b", text, re.IGNORECASE):
        raise RuntimeError(f"No successful response to {command}")
    if require_ok and not any(re.fullmatch(r"\+?OK", line, re.IGNORECASE) for line in lines):
        raise RuntimeError(f"No OK acknowledgment for {command}; inspect the response before retrying")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baud", type=int, default=115200, help="Current USB baud rate (default: 115200)")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().with_name(".env"))
    port = os.environ.get("PORT", "").strip()
    if not port:
        parser.error("PORT environment variable is required; set it in lora/.env")

    try:
        command_file = Path(__file__).resolve().with_name("commands.at")
        commands = read_commands(command_file)
        print(f"Loaded {len(commands)} commands from {command_file}", flush=True)
        with serial.Serial(port, args.baud, timeout=0.1, write_timeout=5, exclusive=True) as radio:
            time.sleep(3)
            exit_attempted = False
            try:
                for command in commands:
                    if command == "AT+EXIT":
                        exit_attempted = True
                    exchange(radio, command, require_ok="=" in command)
                    print("PASS: response check", flush=True)
                time.sleep(3)
            except BaseException:
                if not exit_attempted:
                    try:
                        exchange(radio, "AT+EXIT")
                        time.sleep(3)
                    except (Exception, KeyboardInterrupt) as cleanup_error:
                        print(f"Could not confirm exit from AT mode: {cleanup_error}", file=sys.stderr)
                raise
            print("All command response checks passed; AT mode exited. "
                  "Use receiver.py and transmitter.py to test the radio link.")
        return 0
    except KeyboardInterrupt:
        print("Interrupted. Any accepted settings may have been saved.", file=sys.stderr)
        return 130
    except (serial.SerialException, OSError, ValueError, RuntimeError) as error:
        print(f"AT configuration error: {error}\nAny accepted settings may have been saved. "
              "Check the output before retrying.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
