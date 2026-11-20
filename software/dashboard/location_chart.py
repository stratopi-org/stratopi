"""Time-filtered location altitude chart and per-reading hover details."""

from bisect import bisect_left
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


def add_vertical_speed_arrows(figure, rows, start, end):
    """Place visual direction indicators on an evenly spaced timestamp grid."""
    readings = [row for row in rows if row[1] is not None and isfinite(row[1])]
    if not readings:
        return
    timestamps = [row[0] for row in readings]
    if timestamps[0] == timestamps[-1] or start == end:
        targets = [timestamps[0]]
    else:
        interval_count = 18
        targets = [start + (end - start) * ((index + 0.5) / interval_count)
                   for index in range(interval_count)]
    for target in targets:
        if target < timestamps[0] or target > timestamps[-1]:
            continue
        right = bisect_left(timestamps, target)
        left = max(0, right - 1)
        before, after = readings[left], readings[right]
        nearest = before if target - before[0] <= after[0] - target else after
        speed = float(nearest[2]) if nearest[2] is not None else 0
        if not isfinite(speed) or speed == 0:
            continue
        elapsed = (after[0] - before[0]).total_seconds()
        fraction = (target - before[0]).total_seconds() / elapsed if elapsed else 0
        altitude = float(before[1]) + fraction * (float(after[1]) - float(before[1]))
        figure.add_annotation(
            x=target.isoformat(), y=altitude, xref='x', yref='y',
            text='↑' if speed > 0 else '↓',
            font={'color': '#86dba0' if speed > 0 else '#f38b91', 'size': 20},
            showarrow=False, xanchor='center', yanchor='middle',
        )


def build_location_figure(rows, start, end):
    hover_details = []
    for row in rows:
        numeric_details = [float(value) if value is not None else 'NULL' for value in row[2:5]]
        hover_details.append([*numeric_details, str(row[5]) if row[5] is not None else 'NULL'])
    figure = go.Figure(go.Scatter(
        x=[row[0].astimezone(timezone.utc).isoformat() for row in rows],
        y=[float(row[1]) if row[1] is not None else None for row in rows],
        customdata=hover_details,
        name='altitude_m',
        mode='lines+markers',
        line={'color': '#88c7ff', 'width': 2},
        marker={'symbol': 'circle', 'color': '#a3b1c2', 'size': 4},
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
    add_vertical_speed_arrows(figure, rows, start, end)
    add_y_padding(figure)
    return figure
