# LoRa hello world

Two standalone Python apps for a pair of Waveshare **USB-TO-LoRa-HF** dongles:

- `receiver.py`: the ground app; listens and prints received messages.
- `transmitter.py`: sends `hello world` with the current date and time immediately,
  then every five seconds. Each message uses the transmitting host's local time
  in `%Y-%m-%dT%H:%M:%S` format, for example `hello world 2026-11-23T14:05:09`.

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
device. They exit with an error if it is missing or empty. Set `PORT` in the `.env` file:

```dotenv
PORT="/dev/ttyACM0"
```

Both apps automatically load `lora/.env` at startup, even when launched from a
different directory. Existing environment variables take precedence over `.env`
values. Restart the app after editing `.env` to load the new values.

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

## Inspect and configure a dongle

Stop the receiver/transmitter before opening the same dongle with `set_at.py`.
The script loads `PORT` from `.env`, enters AT mode with CRLF line endings,
prints responses, and sends `AT+EXIT` before closing. It waits three seconds for
startup and again after exiting. See the
[Waveshare AT reference](https://www.waveshare.com/wiki/USB-TO-LoRa-xF).

Edit `lora/commands.at`, then run:

```sh
.venv/bin/python set_at.py
```

All AT commands come from that file, in order. There is no `--set` option.
The file includes entry, firmware/help display, the candidate radio settings,
and exit. **Running the supplied file changes radio settings.** To inspect only,
comment out the `AT+NAME=value` lines, leaving `+++`, `AT+VER`, `AT+HELP`, and
`AT+EXIT`. Blank lines and `#` comments are ignored. The file is resolved relative
to the script, so launching from a different directory works.

The whole file is validated before the serial port opens. It must begin with
`+++` and end with `AT+EXIT`, each appearing exactly once. Unsupported commands
and out-of-range values fail validation. USB baud/parity changes, firmware
updates, factory resets, and encryption changes are not supported by this script.

Each command and response is printed. Setters must return `OK` or `+OK`; all
commands must return more than an echo, without ERROR/ERR/FAIL. Each successful
response check prints PASS. These checks verify acknowledgments, not an actual
radio transmission or persistence after power cycling. Optional query examples
in the file are commented out because readback syntax depends on firmware;
if enabled, query values are displayed but not automatically compared.

For the planned Nashville deployment (three apps reporting every 30 seconds for
up to six hours), target 915 MHz: HF channel 65 (850 + 65 MHz). A candidate
configuration to evaluate is SF10, 500 kHz bandwidth, coding rate 4/5, stream
mode, a shared network ID of 42, address 0, LBT enabled, and RSSI output disabled.
Start nearby testing at 10 dBm; choose field power from the dongle's US approval
and range tests. SF10 is an engineering starting point, not a validated flight
profile. Payload lengths and flight distance still determine airtime and range.
See [Semtech's sensitivity/airtime explanation](https://www.semtech.com/design-support/faq/faq-lora).

US fixed-frequency digital operation under
[47 CFR 15.247](https://www.govinfo.gov/content/pkg/CFR-2025-title47-vol1/xhtml/CFR-2025-title47-vol1-sec15-247.html)
has a minimum 6 dB bandwidth requirement of 500 kHz. Selecting BW=2 alone does
not establish compliance: confirm the exact dongle's FCC authorization, permitted
settings, and antenna before deployment. The earlier generic 125 kHz suggestion
is not a verified US fixed-channel operating profile.

The supplied `commands.at` contains this candidate configuration. Run it on
each dongle separately, with the appropriate `PORT` on each host.

Keep RSSI output disabled because the current receiver expects newline-delimited
UTF-8 messages. A network ID separates networks; it does not provide encryption
or authentication. The apps run on separate hosts. When multiple hosts transmit
on the same channel, stagger their 30-second reporting cycles (for example,
offsets of 0, 10, and 20 seconds for three transmitters). LBT helps reduce
collisions but does not guarantee delivery. Three reports every 30 seconds
amount to 2,160 reports per six-hour run. Scheduling offsets are not implemented
by the current hello-world apps.

Supported settings are `SF` (7–12), `BW` (0–2), `CR` (1–4), `PWR` (10–22),
`NETID` (0–255), `LBT` (0–1), `MODE` (1–3), `TXCH`/`RXCH` (0–80),
`RSSI` (0–1), and `ADDR` (0–65535). `--baud` selects the dongle's current USB
baud rate; the script does not change the USB baud rate, parity, or encryption key.

Settings require an `OK` or `+OK` acknowledgment. The script stops on errors,
timeouts, or unrecognized acknowledgments and attempts to exit AT mode. EXIT
saves accepted settings, so a failed run can leave partial changes; this is not
an atomic update or rollback. Inspect the transcript before retrying. Successful
acknowledgments do not replace a radio link test. Protocol behavior has been
checked with simulated serial responses; physical dongle configuration still
needs verification.

## Recovery and radio testing

These radio parameter changes are generally recoverable through the USB AT
interface, which keeps its existing baud rate and parity. Mismatched radio
settings can break the wireless link until both sides match. There is no
transactional rollback: `AT+EXIT` can save setters accepted before a later error.
The script attempts EXIT on failure and reports cleanup failures without hiding
the original error. It never configures connected hardware just by being installed.

After configuring both ends:

1. Start `.venv/bin/python receiver.py` on the receiving host.
2. Run `.venv/bin/python transmitter.py --once` on the transmitting host.
3. Confirm `hello world` appears on the receiver. Sender output alone does not
   confirm reception.
4. Power-cycle both dongles and repeat to check settings persistence, then test
   sustained reports and range using the planned antennas and payload sizes.

Serial protocol tests use simulated dongles; the supplied configuration has not
been applied to physical hardware by this development session.
