# StratoPi dashboard

A Python 3.14.10 / Flask application that displays paginated rows and column headers
from every visible PostgreSQL user table, ordered by schema and table name.
Navigation links and table headings display only the table name, without schema
prefixes such as `public.`.
Timestamp values in `added` columns use a readable format such as
`Nov 4 8:55:56 PM`, with no leading zero on the day or hour and a space before
AM/PM, preserving the timezone returned by PostgreSQL.
Valid values in `coordinates` columns link to Google Maps in a new tab using
`https://www.google.com/maps/search/?api=1&query=latitude,longitude`.
PostgreSQL POINT values are stored as `(longitude,latitude)` and reversed for
the link. Invalid coordinates remain plain text; NULL values remain explicit.
Coordinate links retain the normal cell spacing without extra indentation or
line breaks from template formatting.
`vertical_speed_mpm` values are green when positive and red when negative;
zero and NULL retain their neutral styling.
`direction` columns show an arrow beside valid compass directions (N, NE, E,
SE, S, SW, W, NW), pointing in the corresponding direction. Matching ignores
case and surrounding whitespace; invalid values stay plain text.
Each non-null `id` appears as a compact ID-card icon. Hover, focus with the
keyboard, or tap the icon to reveal the full, selectable ID in a popover.
Click, tap, or activate the icon with Enter/Space to copy the full ID and show
“id copied to clipboard.” for three seconds in a muted blue
notification. Clipboard access
requires localhost or HTTPS and browser permission; failures show a message
so the ID can be copied manually from the popover.
Press Escape to dismiss it. NULL IDs remain explicit.
The frontend uses server-rendered HTML, CSS, and a small JavaScript file for
ID popovers and in-place data refreshes; no JavaScript build is needed.
The dashboard always uses dark mode, including table headers, row hover states,
buttons, notices, and keyboard focus indicators.

## Run locally

```sh
cd dashboard
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
touch .env
```

Set `POSTGRES_URL` in `.env` to your PostgreSQL connection URL _(the same setting
used by the other StratoPi software)_, then run:

```sh
.venv/bin/python -m flask --app app run --host 0.0.0.0 --port 5500
```

Open <http://127.0.0.1:5500> for the Charts page.
The lowercase `battery` and `environmental` header links jump to matching sections.
The `battery` section contains the battery chart, and `environmental` contains
all four environmental charts.
The Charts page has a compact time picker in the upper right. Open it to select a quick
range of 5, 15, or 30 minutes, or 1, 2, 3, 6, 12, or 24 hours.
All available data selects the earliest through latest finite `added` timestamp
across visible user tables. It sets the shared Charts time window to the full
recorded history. Reloading recalculates those bounds to include new records.
With no saved range in the URL, Charts defaults to the last 3 hours, from now
minus 3 hours to now. With no saved Charts auto-refresh preference, Auto refresh
starts at Never. The selected dates also prefill the absolute From and To fields.
Quick ranges end at the current
time. Retired presets such as 1 minute, 7 days, and 30 days fall back
to the 3-hour default when encountered in an older URL.
For a custom range, choose From and To dates and times, then Apply time range.
Dates use the browser's timezone, shown inside the picker. Invalid or reversed
ranges show a validation message. Escape or clicking outside closes the picker.
The selected inclusive range is saved as UTC `start` and `end` URL parameters.
Quick selections also save a `range` parameter and recalculate relative to the
current time when the page reloads. Custom dates stay fixed across reloads.
Charts data and graphs read `#charts-time-range`'s `data-start` and
`data-end` and listen for the bubbling `charts:range-change` event, whose detail
contains the same ISO timestamps.
The Charts page has its own Auto refresh selector with Never (default), 15, 30, and
60-second intervals and Every 2 minutes, remembered separately from the Data page. Enabling it
refreshes immediately. The browser requests each chart's Flask JSON endpoint,
and Flask runs read-only, time-filtered PostgreSQL queries. Plotly updates the
charts in place. This is periodic polling, with one query per chart per cycle.
Relative ranges advance to the current time on each cycle. Custom absolute
ranges keep their selected dates. All available data first fetches new database
time bounds so newly recorded data is included. The next interval begins after
all chart requests and renders finish. Failed cycles retry at the next interval.
A seconds-ago status updates after a successful cycle and clears on Never.
The `battery` chart plots `public.battery.percent` and `temperature_c` against
`added`, oldest first, on a shared X axis. Percent uses the left Y axis and
temperature_c uses the right Y axis, each with its own scale. Blue represents percent
and amber represents temperature in °C. Hover shows both readings at a time.
The chart uses the browser's timezone to match the picker, with the X axis
labeled simply `added`. Changing any time
selection reloads every Charts chart with inclusive start/end SQL filters.
Plotly Python builds the figure returned by `/api/charts/battery`; Plotly.js
renders it in place. Its JavaScript bundle is served locally from the installed
Python package. Empty selections and database errors display a status message.
Rapid range changes cancel previous requests so stale results cannot overwrite
the current chart. Charts fetch all matching readings, independent of Data's
30-row pagination.
Every chart gives each Y axis at least 10% of its data span as padding below
the minimum and above the maximum. The calculated endpoints use Plotly's
`autorangeoptions.include`, keeping autorange and native zoom/reset behavior.
Constant readings use 10% of their absolute value as padding, with a 0.1-unit
fallback for zero. Missing and non-finite values do not affect the calculation.
Padding is recalculated for each selected time range, independently per Y axis.
Four environmental charts use the same Charts time filter and `added` X axis.
“temperature” plots `in_temperature_c` and `ex_temperature_c` in °C.
“pressure” plots `in_pressure_hpa` and `ex_pressure_hpa` in hPa.
“humidity” plots `in_humidity_rh` and `ex_humidity_rh` in % RH.
“cpu temperature” plots `cpu_temperature_c` in °C.
Paired readings use independent Y scales, with blue internal readings labeled
on the left and amber external readings labeled on the right. CPU temperature
uses one left Y axis. Missing sensor values
remain gaps. The environmental figures are served by
`/api/charts/environmental/<chart>` using the same inclusive date filtering.
The picker is disabled when timestamps are unavailable or the database cannot
be reached. Naive database timestamps use the PostgreSQL session timezone.
Use the navigation to open Data at `/data` or return to Charts.
The top navigation uses padded pills and highlights the current page.
On Data, each table has independent Previous/Next controls
with 30 rows per page, a total row count, and a page and row-range indicator
such as “Page **2** of 2. Row 31 - 45.” with the current page number bolded
and highlighted with a subtle background and brighter text, without a border.
Table headers show “1 row” for a single row and “rows” for all other counts.
Tables expand vertically to fit all rows on the current page (up to 30), with
horizontal scrolling available for wide tables.
The entire pagination bar is hidden for tables with only one page, including
empty tables. Changing one
table's page preserves the others and returns to that table. Page selections
are stored in the URL.
Auto refresh offers Never (the default), Every 15 seconds, Every 30 seconds,
Every 60 seconds, and Every 2 minutes. The browser remembers the selection across page navigation.
Previously saved 5-second preferences fall back to Never on both pages.
Automatic refresh fetches fresh table HTML and replaces
the data in place without a full page reload. This is polling rather than a
continuous stream. Selected table pages and scroll position are preserved;
failed requests retain the existing data and automatic refresh retries on the
next interval. Requests never overlap; the interval starts after each finishes.
After a successful refresh, the status reads “Data refreshed X seconds ago”
and updates every second, resetting after the next successful refresh.
Selecting Never clears the elapsed-time message and stops its timer.
Enabling or changing an automatic refresh interval fetches data immediately,
then starts the selected interval after completion. Re-enabling auto refresh
resets the elapsed-time label after that fresh request succeeds.
An exported `POSTGRES_URL` takes precedence over `.env`.

Queries run in a read-only transaction with a 30-second statement timeout.
Use a database account with SELECT access to the intended schemas/tables.
System schemas are excluded; empty tables still show their column headers.
Rows are ordered by `added ASC` (oldest first), with PostgreSQL's physical row
location breaking timestamp ties. Tables without `added` use physical row order.
UUID IDs are not used for sorting. Changes to the data between requests
can shift page boundaries. NULL is displayed explicitly and HTML values are
escaped. Only 30 rows per table are fetched per request; counting rows and large
page offsets can still take time on large tables. Invalid pages default to 1;
out-of-range pages are clamped to the available range.

This initial app binds locally and has no authentication.

## Checks

```sh
.venv/bin/python -m unittest discover -s tests
node --test tests/*.cjs
```

## Development conventions

Follow [AGENTS.md](AGENTS.md) when working on this application.
