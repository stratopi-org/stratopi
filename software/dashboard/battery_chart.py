"""Read battery readings and build the shared-time-range Plotly figure."""

from datetime import timezone

import plotly.graph_objects as go

from chart_style import add_y_padding, chart_layout
from database import read_connection


def read_battery(database_url, start, end):
    with read_connection(database_url) as connection:
        connection.read_only = True
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '30s'")
            cursor.execute("""
                SELECT added, percent, temperature_c
                FROM public.battery
                WHERE added >= %s AND added <= %s
                ORDER BY added ASC
            """, (start, end))
            return cursor.fetchall()


def build_battery_figure(rows, start, end):
    timestamps = [row[0].astimezone(timezone.utc).isoformat() for row in rows]
    figure = go.Figure()
    for index, name, unit, color in [
        (1, 'percent', '%', '#88c7ff'),
        (2, 'temperature_c', '°C', '#f3b875'),
    ]:
        figure.add_trace(go.Scatter(
            x=timestamps,
            y=[float(row[index]) if row[index] is not None else None for row in rows],
            name=name,
            yaxis='y' if name == 'percent' else 'y2',
            mode='lines+markers',
            line={'color': color, 'width': 2},
            marker={'size': 4},
            hovertemplate=f'%{{y}} {unit}<extra>{name}</extra>',
            connectgaps=False,
        ))
    figure.update_layout(
        chart_layout('battery', start, end),
        margin={'t': 65, 'r': 80, 'b': 70, 'l': 65},
        yaxis={'title': {'text': 'percent (%)', 'font': {'color': '#88c7ff'}},
               'tickfont': {'color': '#88c7ff'}, 'side': 'left',
               'gridcolor': '#2b3747', 'zeroline': False},
        yaxis2={'title': {'text': 'temperature_c (°C)', 'font': {'color': '#f3b875'}},
                'tickfont': {'color': '#f3b875'}, 'overlaying': 'y', 'side': 'right',
                'showgrid': False, 'zeroline': False},
        meta={'row_count': len(rows)},
    )
    add_y_padding(figure)
    return figure
