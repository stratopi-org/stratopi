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
`+++`, followed immediately by `AT+VER`, and end with `AT+EXIT`, with entry/exit
each appearing exactly once. Unsupported commands
and out-of-range values fail validation. USB baud/parity changes, firmware
updates, factory resets, and encryption changes are not supported by this script.

Each command and response is printed. Setters must return `OK` or `+OK`; all
ordinary AT commands must return more than an echo, without ERROR/ERR/FAIL.
The dongle may echo only `+++` on entry; the script accepts that and checks the
following `AT+VER` response before sending any settings. Each successful
response check prints PASS. Your Ver1.2 firmware's help confirms `AT+NAME?`
readback support. The supplied file reads the initial TXCH/RXCH/SF values and
queries every setting immediately after writing it. Queries must return OK and
one numeric value (plain or labeled with the setting name); a value that differs
from the preceding setter fails the run. Unrecognized formats also fail with
the raw response displayed so they can be diagnosed.

The script pauses one second between commands to give firmware time to finish
reconfiguring after an acknowledgment. This is a timing precaution, not a
confirmed explanation of the observed silence after RXCH. These checks verify
responses and readback values, not actual radio reception or persistence after
power cycling. A failure stops further setters and attempts EXIT; it does not
retry commands automatically or treat silence as success.

For the planned Nashville deployment (three apps reporting every 30 seconds for
up to six hours), target 915 MHz: HF channel 65 (850 + 65 MHz). A candidate
flight configuration to evaluate is SF10, 500 kHz bandwidth, coding rate 4/6, stream
mode, a shared network ID of 42, address 479, LBT enabled, and RSSI output disabled.
The file now requests 22 dBm (about 158 mW), the module maximum; confirm that
power and antenna are permitted by the exact dongle's US authorization. This is
an engineering starting point, not a validated flight profile or guaranteed
range. Payload lengths and flight distance still determine airtime and range.
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

For setters, the script waits up to five seconds for an acknowledgment even if
the command echo arrives immediately. An echo followed by a quiet interval does
not count as completion. Timeout diagnostics distinguish no response, echo-only
responses, and explicit firmware errors. If a run fails, retain the full output
from `+++` onward so the firmware response can be diagnosed; silence is not
treated as success.

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

## Flight profile rationale: 100,000 feet

The active flight profile uses the following settings after hardware troubleshooting:

- `AT+SF=10`: retain the setting that restored messaging after SF12 failed in
  hardware tests. The root cause of the SF12 failure is unconfirmed. SF10 has
  shorter airtime and lower energy per message than SF12, but less weak-signal
  sensitivity. Flight range remains unverified.
- `AT+CR=1` -> `AT+CR=2`: changes coding rate from 4/5 to 4/6, adding redundancy
  for error correction. Payload coding overhead increases by about 20%; total
  packet overhead increases less because preamble/header costs differ. This can
  help with some errors, but does not recover every faded or collided packet.
  Higher 4/7 or 4/8 settings cost still more airtime, so they are not selected
  without packet-loss measurements showing a benefit.
- `AT+PWR=18` -> `AT+PWR=22`: restores maximum RF output from about 63 mW to
  about 158 mW, a 4 dB increase. This adds link margin but increases transmit
  current and battery use. It does not mean 2.5 times the range or 2.5 times
  total electrical consumption. Verify the power supply under transmit load.

These are engineering tradeoffs based on the
[Semtech SX1261/2 datasheet](https://cdn.sparkfun.com/assets/6/b/5/1/4/SX1262_datasheet.pdf)
and the [Waveshare AT reference](https://www.waveshare.com/wiki/USB-TO-LoRa-xF).

Settings retained and why:

- `TXCH=65`, `RXCH=65`: keep a shared 915 MHz center frequency. A different
  channel can help measured local interference, but there is no universally
  best channel and no spectrum measurement here.
- `BW=2`: retain 500 kHz for the existing US fixed-frequency plan. Narrower
  bandwidth can improve sensitivity but lengthens airtime; the current choice
  is not proof of FCC authorization for the dongle/antenna combination.
- `MODE=1`: retain transparent stream mode for the existing Python message format.
- `NETID=42`, `ADDR=479`: retain nondefault traffic filters and interoperability.
  Neither authenticates the sender.
- `LBT=1`: retain listen-before-talk to help with busy-channel collisions. It
  can add up to two seconds of delay, after which this firmware can transmit
  anyway; it is not a delivery guarantee or scheduled access mechanism.
- `RSSI=0`: retain compatibility with the UTF-8 receiver. Enabling it adds binary
  bytes to received data; signal-strength logging needs receiver changes first.
- CRC remains enabled by the dongle firmware. No CRC command is needed. USB
  baud/parity and encryption configuration remain unchanged.

For scale, a calculated 100-byte LoRa payload with explicit header, CRC,
8-symbol preamble and no low-data-rate optimization takes about 0.26 seconds
at the old SF10/BW500/4-5 setting versus 0.30 second at the current
SF10/BW500/4-6 setting. Those assumptions are
illustrative: the dongle's actual preamble, framing overhead and packetization
must be measured. Three such transmissions per 30 seconds would occupy about
3% of the shared channel before retries or LBT delays. Keep telemetry compact,
stagger independent transmitting hosts, and test actual payloads. The current
hello-world transmitter still defaults to five seconds; use `--interval 30` for
the proposed reporting cadence. The AT file does not schedule application sends.

## Drift and radio-distance planning

100,000 feet is 30.48 km of altitude. Altitude alone does not determine landing
position. Wind direction and speed vary with height and time; ascent rate,
burst altitude, descent profile and any float time all matter.

The project design assumption is now **up to 500 km (311 miles) horizontal drift**,
as requested. This is a planning target, not a forecast or a guaranteed maximum.
No launch date/time or ascent/descent profile is available yet.

As context, [NOAA's radiosonde factsheet](https://www.weather.gov/upperair/factsheet)
reports that flights exceeding two hours can drift more than 300 km (about
180 miles). Evaluate shorter 100–300 km separations as well as the requested
500 km target; none is a Nashville forecast or a predicted landing radius.
A six-hour flight can go farther.
For illustration only, a constant net horizontal velocity of 10–20 m/s over
three hours yields 108–216 km (67–134 miles); over six hours, 216–432 km
(134–268 miles). Actual displacement is the vector sum of changing winds,
not surface wind speed multiplied by total flight time.

Use the [SondeHub/CUSF predictor](https://predict.sondehub.org/) with the launch
coordinates/time, 30,480 m target altitude, expected ascent and descent rates,
and current wind forecasts. Repeat near launch and compare scenarios with
uncertain ascent/descent rates. A latex burst-flight prediction is not a model
of a six-hour controlled float flight.

Calculated geometric horizon at 30.48 km above the ground and a 2 m receiver
antenna is approximately 628 km (390 miles), using spherical Earth radius
6,371 km and no atmospheric refraction. This is a visibility limit, not a radio
range guarantee. At 200 km horizontal separation, the slant path is about
202 km. At the requested 500 km separation, spherical-Earth geometry gives
about 502 km slant range and only 1.2 degrees elevation to the balloon for a
near-ground observer. Local obstructions are therefore particularly important.

An illustrative free-space calculation at 915 MHz and 502 km gives about
145.7 dB path loss. With 22 dBm transmit power, 0 dBi effective antenna gain
at each end, and 2 dB combined additional loss, received power is roughly
-125.7 dBm. The earlier SF12 calculation used Semtech's typical -129 dBm
boosted-mode sensitivity at BW500 (excluding RF switch loss), leaving only
about 3 dB of illustrative margin. That optimistic SF12 calculation is not a
link budget for the current SF10 setting, which has lower sensitivity. The
current SF10 profile does not establish a robust 500 km link. The dongle's
receive mode, implementation losses, actual antenna
patterns, polarization and interference are not characterized here. Ground
antenna gain and tracking/placement could improve the link substantially,
but must be checked against authorized antenna/power combinations. The
maximum AT settings alone do not establish a reliable 500 km system.

Antenna orientation, payload rotation, cable loss, interference and
receiver placement can dominate the link. As the payload descends, its horizon
shrinks; terrain and buildings can block reception, especially after landing.
Use a mobile recovery receiver rather than assuming a launch-site receiver
will retain contact throughout recovery.

An additional hardware limit matters at this altitude: Waveshare specifies
0–85 C for the TCXO dongle and 0–50 C for the XTAL variant. An exposed dongle
is not rated for stratospheric cold. Keep the radio within its specified range
using a tested payload thermal design; AT tuning cannot compensate for it.
See [Waveshare's product specifications](https://www.waveshare.com/product/usb-to-lora.htm).
