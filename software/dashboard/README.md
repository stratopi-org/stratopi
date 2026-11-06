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
.venv/bin/python -m flask --app app run --host 127.0.0.1 --port 5000
```

Open <http://127.0.0.1:5000>. Each table has independent Previous/Next controls
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
Auto refresh offers Never (the default), Every 5 seconds, Every 15 seconds, Every 30 seconds,
and Every 60 seconds. The browser remembers the selection across page navigation.
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
