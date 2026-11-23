# LoRa hello world

Two standalone Python apps for a pair of Waveshare **USB-TO-LoRa-HF** dongles:

- `receiver.py`: the ground app; listens and prints received messages.
- `transmitter.py`: sends `hello world` immediately, then every five seconds.

## Hardware setup

Attach the matching antennas and plug one dongle into each computer. Both radios
must use matching radio settings (including transmit/receive channel, network ID,
air rate, address, and encryption key) and transparent/stream mode. These apps use
the dongles' existing radio configuration; they do not send configuration commands.

According to [Waveshare's documentation](https://www.waveshare.com/wiki/USB-TO-LoRa-xF),
the default USB serial settings are **115200 baud, 8 data bits, no parity, 1 stop
bit**, and transparent transmission is the default mode. The HF factory transmit
and receive channels are both 18 (868 MHz), with network ID and address 0 and
encryption disabled. Use a matching channel permitted at your location. If your
dongles were previously configured, check their settings using Waveshare's AT
configuration instructions and exit command mode before running these apps.

This is a point-to-point LoRa serial link, with no pairing handshake or delivery
acknowledgments. The transmitter's output confirms a write to its USB dongle;
seeing `hello world` on the receiver confirms reception.

## Install on both computers

From `software/lora`:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m serial.tools.list_ports -v
```

Use the device listed for your dongle. Linux commonly uses `/dev/ttyACM0` or
`/dev/ttyUSB0`; macOS uses `/dev/cu.usbmodem...` or `/dev/cu.usbserial...`;
Windows uses `COM3` or similar. On Linux, your account may need membership in
the device's serial-access group (commonly `dialout`). Only one app should open
each dongle at a time.

## Run

Both apps require the `PORT` environment variable to identify the USB serial
device. They exit with an error if it is missing or empty. Set `PORT` in the `.env` file.


On the ground computer, start the receiver first:

```sh
.venv/bin/python receiver.py
```

On the transmitting computer:

```sh
.venv/bin/python transmitter.py
```

If both dongles are attached to one computer, select a different port for each.
The receiver prints each complete newline-delimited message, retaining partial
messages across serial read timeouts. Press Ctrl-C to stop either app.

Optional transmitter controls:

```sh
PORT=/dev/ttyACM0 .venv/bin/python transmitter.py --once
PORT=/dev/ttyACM0 .venv/bin/python transmitter.py --interval 10
```

Both apps accept `--baud` if your dongles use a different USB serial baud rate.
Changing this flag does not change their over-the-air settings.
