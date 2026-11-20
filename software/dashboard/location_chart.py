"""Time-filtered location altitude chart and per-reading hover details."""

from datetime import timezone
from math import isfinite

import plotly.graph_objects as go

from chart_style import add_y_padding, chart_layout
from database import read_connection


def read_location(database_url, start, end):
    with read_connection(database_url) as connection:
        connection.read_only = True
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '30s'")
            cursor.execute("""
                SELECT added, altitude_m, vertical_speed_mpm, speed_kn, course_d, direction
                FROM public.location
                WHERE added >= %s AND added <= %s
                ORDER BY added ASC
            """, (start, end))
            return cursor.fetchall()


def select_arrow_readings(rows, start, end):
    """Keep the strongest ascent/descent reading in each of 12 time intervals."""
    interval_seconds = max((end - start).total_seconds() / 12, 0.000001)
    intervals = {}
    for index, row in enumerate(rows):
        if row[1] is None or row[2] is None:
            continue
        speed = float(row[2])
        if not isfinite(speed) or speed == 0:
            continue
        interval = min(11, max(0, int((row[0] - start).total_seconds() / interval_seconds)))
        previous = intervals.get(interval)
        if previous is None or abs(speed) > previous[0]:
            intervals[interval] = (abs(speed), index)
    return {index for speed, index in intervals.values()}


def build_location_figure(rows, start, end):
    arrow_readings = select_arrow_readings(rows, start, end)
    hover_details = []
    markers = {'symbol': [], 'color': [], 'size': []}
    for index, row in enumerate(rows):
        numeric_details = [float(value) if value is not None else 'NULL' for value in row[2:5]]
        hover_details.append([*numeric_details, str(row[5]) if row[5] is not None else 'NULL'])
        vertical_speed = float(row[2]) if row[2] is not None else 0
        if index not in arrow_readings:
            symbol, color, size = 'circle', '#a3b1c2', 4
        elif vertical_speed > 0:
            symbol, color, size = 'arrow-up', '#86dba0', 10
        else:
            symbol, color, size = 'arrow-down', '#f38b91', 10
        markers['symbol'].append(symbol)
        markers['color'].append(color)
        markers['size'].append(size)
    figure = go.Figure(go.Scatter(
        x=[row[0].astimezone(timezone.utc).isoformat() for row in rows],
        y=[float(row[1]) if row[1] is not None else None for row in rows],
        customdata=hover_details,
        name='altitude_m',
        mode='lines+markers',
        line={'color': '#88c7ff', 'width': 2},
        marker=markers,
        hovertemplate=(
            'altitude_m: %{y} m<br>'
            'vertical_speed_mpm: %{customdata[0]} m/min<br>'
            'speed_kn: %{customdata[1]} kn<br>'
            'course_d: %{customdata[2]}°<br>'
            'direction: %{customdata[3]}<extra></extra>'
        ),
        connectgaps=False,
    ))
    figure.update_layout(
        chart_layout('altitude', start, end),
        yaxis_title='altitude_m (m)',
        meta={'row_count': len(rows)},
    )
    add_y_padding(figure)
    return figure
