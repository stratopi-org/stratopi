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
    if commands[1] != "AT+VER":
        raise ValueError("AT+VER must immediately follow +++ to confirm AT mode before settings")
    return commands


def exchange(radio, command: str, *, require_ok: bool = False) -> str:
    """Wait up to five seconds; echoes alone must not end a setter's read."""
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
            # Echoes can arrive before the firmware finishes applying a setter.
            # Only ordinary responses use the quiet-period shortcut.
            if not require_ok:
                break
        if response.endswith((b"\r", b"\n")):
            received_lines = response.decode("utf-8", errors="replace").splitlines()
            if any(re.fullmatch(r"\+?OK", line.strip(), re.IGNORECASE) for line in received_lines):
                break
    text = response.decode("utf-8", errors="replace").strip()
    print(text or "(no response)", flush=True)
    lines = [line.strip() for line in text.splitlines() if line.strip() and line.strip() != command]
    # Some firmware echoes only +++ on entry. AT+VER confirms entry next;
    # echo-only replies to ordinary AT commands must still fail.
    entry_echo = command == "+++" and text == "+++"
    if not text:
        raise RuntimeError(f"Timed out waiting for any response to {command}")
    if re.search(r"\b(?:ERROR|ERR|FAIL|FAILED)\b", text, re.IGNORECASE):
        raise RuntimeError(f"Dongle reported an error for {command}: {text!r}")
    if not lines and not entry_echo:
        raise RuntimeError(f"Only an echo received for {command}; command success is unconfirmed")
    if require_ok and not any(re.fullmatch(r"\+?OK", line, re.IGNORECASE) for line in lines):
        raise RuntimeError(f"No OK acknowledgment for {command}; inspect the response before retrying")
    return text


def readback_value(command: str, response: str) -> int:
    """Accept a single integer, optionally labeled with the queried setting."""
    name = command[3:-1]
    values = []
    for raw in response.splitlines():
        line = raw.strip()
        if not line or line == command or re.fullmatch(r"\+?OK", line, re.IGNORECASE):
            continue
        match = re.fullmatch(rf"(?:\+?{name}\s*[:=]\s*)?(\d+)", line, re.IGNORECASE)
        if match:
            values.append(int(match[1]))
    if len(values) != 1:
        raise RuntimeError(f"Cannot interpret readback for {command}: {response!r}")
    return values[0]


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
            expected = {}
            try:
                for command in commands:
                    if command == "AT+EXIT":
                        exit_attempted = True
                    response = exchange(radio, command, require_ok="=" in command or command.endswith("?"))
                    if "=" in command:
                        name, value = command[3:].split("=", 1)
                        expected[name] = int(value)
                    if command.endswith("?"):
                        name = command[3:-1]
                        value = readback_value(command, response)
                        if name in expected and value != expected[name]:
                            raise RuntimeError(f"Readback mismatch for {name}: requested {expected[name]}, got {value}")
                        print(f"Readback {name}={value}" + (" matches requested value." if name in expected else "."), flush=True)
                    print("Entry sent; confirming AT mode with AT+VER next." if command == "+++"
                          else "PASS: response check", flush=True)
                    if command != "AT+EXIT":
                        # Leave time for firmware/radio reconfiguration after OK.
                        time.sleep(1)
                time.sleep(3)
            except BaseException:
                if not exit_attempted:
                    try:
                        exchange(radio, "AT+EXIT")
                        time.sleep(3)
                    except (Exception, KeyboardInterrupt) as cleanup_error:
                        print(f"Could not confirm exit from AT mode: {cleanup_error}", file=sys.stderr)
                raise
            print("All command response checks passed; AT mode exited.")
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
