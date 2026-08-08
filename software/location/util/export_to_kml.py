import datetime
import html
import os
import tempfile

import psycopg2
import simplekml
from lib import common, log

POSTGRES_URL = os.environ["POSTGRES_URL"]

ROUTE_COLOR = simplekml.Color.rgb(30, 110, 255)
ROUTE_WIDTH = 3

POINT_ICON_URL = (
    "https://maps.google.com/mapfiles/kml/paddle/red-circle.png"
)


def format_kml_number(value, decimals=1, suffix=""):
    """Format numbers and numeric strings for the KML description."""
    if value is None:
        return "Unknown"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return html.escape(str(value))

    return f"{value:,.{decimals}f}{suffix}"


def timestamp_to_iso8601(timestamp):
    """Return a timestamp in UTC ISO-8601 format."""
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)

    return (
        timestamp.astimezone(datetime.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def build_description(
    timestamp_iso,
    altitude_m,
    speed_kn,
    course_d,
    direction,
):
    """Build the details shown when a point is selected."""
    altitude_ft = (
        common.meters_to_feet(altitude_m)
        if altitude_m is not None
        else None
    )

    speed_mps = (
        common.knots_to_mps(speed_kn)
        if speed_kn is not None
        else None
    )

    speed_mph = (
        common.knots_to_mph(speed_kn)
        if speed_kn is not None
        else None
    )

    date_time = html.escape(timestamp_iso)
    direction_text = html.escape(str(direction or "Unknown"))

    altitude = (
        f"{format_kml_number(altitude_m, 1, ' m')} / "
        f"{format_kml_number(altitude_ft, 0, ' ft')}"
    )

    speed = (
        f"{format_kml_number(speed_kn, 1, ' kn')} / "
        f"{format_kml_number(speed_mps, 1, ' m/s')} / "
        f"{format_kml_number(speed_mph, 1, ' mph')}"
    )

    course = format_kml_number(course_d, 1, "°")

    return (
        '<div style="font-family:Arial,sans-serif;font-size:14px;">'

        '<div style="margin-bottom:12px;">'
        '<div><b>Date and time</b></div>'
        f'<div>{date_time}</div>'
        '</div>'

        '<div style="margin-bottom:12px;">'
        '<div><b>Altitude</b></div>'
        f'<div>{altitude}</div>'
        '</div>'

        '<div style="margin-bottom:12px;">'
        '<div><b>Speed</b></div>'
        f'<div>{speed}</div>'
        '</div>'

        '<div style="margin-bottom:12px;">'
        '<div><b>Course</b></div>'
        f'<div>{course}</div>'
        '</div>'

        '<div>'
        '<div><b>Direction</b></div>'
        f'<div>{direction_text}</div>'
        '</div>'

        '</div>'
    )


def fetch_locations():
    """Retrieve all recorded locations in chronological order."""
    query = """
        SELECT
            (date + time)::timestamp AS timestamp,
            coordinates[0] AS longitude,
            coordinates[1] AS latitude,
            altitude_m,
            speed_kn,
            course_d,
            direction
        FROM location
        WHERE
            coordinates[0] IS NOT NULL
            AND coordinates[1] IS NOT NULL
        ORDER BY timestamp ASC;
    """

    masked_postgres_url = common.mask_postgres_url_password(
        POSTGRES_URL
    )

    with psycopg2.connect(POSTGRES_URL) as connection:
        log.debug(
            f"connected to PostgreSQL ({masked_postgres_url})"
        )

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    log.debug("closed PostgreSQL connection")

    return rows


def create_point_style():
    """Create the shared style used by all recorded points."""
    style = simplekml.Style()

    style.iconstyle.icon.href = POINT_ICON_URL

    # The previous value was 0.55.
    style.iconstyle.scale = 1.0

    style.labelstyle.scale = 0.75
    style.labelstyle.color = simplekml.Color.white

    return style


def add_route(kml, rows):
    """Add the complete GPS route to the KML document."""
    route_folder = kml.newfolder(name="Route")

    route = route_folder.newlinestring(
        name="StratoPi flight path"
    )

    route.altitudemode = simplekml.AltitudeMode.absolute

    # Prevent Google Earth from drawing vertical walls between
    # the route and the ground.
    route.extrude = 0
    route.tessellate = 0

    route.style.linestyle.width = ROUTE_WIDTH
    route.style.linestyle.color = ROUTE_COLOR

    route.coords = [
        (
            longitude,
            latitude,
            altitude_m if altitude_m is not None else 0,
        )
        for (
            _timestamp,
            longitude,
            latitude,
            altitude_m,
            _speed_kn,
            _course_d,
            _direction,
        ) in rows
    ]


def add_points(kml, rows):
    """Add a selectable, labeled marker for every GPS point."""
    points_folder = kml.newfolder(name="Recorded locations")
    point_style = create_point_style()
    last_index = len(rows) - 1

    for index, row in enumerate(rows):
        (
            timestamp,
            longitude,
            latitude,
            altitude_m,
            speed_kn,
            course_d,
            direction,
        ) = row

        point_number = index + 1
        timestamp_iso = timestamp_to_iso8601(timestamp)

        if index == 0:
            point_name = f"#{point_number} — Start"
        elif index == last_index:
            point_name = f"#{point_number} — End"
        else:
            point_name = f"#{point_number}"

        point = points_folder.newpoint(
            name=point_name,
            coords=[
                (
                    longitude,
                    latitude,
                    altitude_m if altitude_m is not None else 0,
                )
            ],
        )

        point.altitudemode = simplekml.AltitudeMode.absolute

        point.description = build_description(
            timestamp_iso=timestamp_iso,
            altitude_m=altitude_m,
            speed_kn=speed_kn,
            course_d=course_d,
            direction=direction,
        )

        point.style = point_style


def export_kml():
    """Export the recorded location history to a KML file."""
    rows = fetch_locations()

    if not rows:
        log.warning(
            "no recorded locations found; KML export not created"
        )
        return None

    created_at = datetime.datetime.now(datetime.timezone.utc)
    filename_timestamp = created_at.strftime(
        "%Y_%m_%d_%H_%M_%S"
    )

    kml_file = os.path.join(
        tempfile.gettempdir(),
        f"stratopi_location_{filename_timestamp}.kml",
    )

    kml = simplekml.Kml(
        name=f"StratoPi {created_at:%Y-%m-%d %H:%M UTC}"
    )

    add_route(kml, rows)
    add_points(kml, rows)

    kml.save(kml_file)

    log.info(
        f"successfully created KML export '{kml_file}' "
        f"with {len(rows):,} recorded locations"
    )

    return kml_file


if __name__ == "__main__":
    export_kml()
