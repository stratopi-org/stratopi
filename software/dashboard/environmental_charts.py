"""Time-filtered environmental charts for Charts."""

from datetime import timezone

import plotly.graph_objects as go
import psycopg
from psycopg import sql

from chart_style import add_y_padding, chart_layout


ENVIRONMENTAL_CHARTS = {
    'temperature': {
        'title': 'temperature',
        'columns': ('in_temperature_c', 'ex_temperature_c'),
        'unit': '°C',
    },
    'pressure': {
        'title': 'pressure',
        'columns': ('in_pressure_hpa', 'ex_pressure_hpa'),
        'unit': 'hPa',
    },
    'humidity': {
        'title': 'humidity',
        'columns': ('in_humidity_rh', 'ex_humidity_rh'),
        'unit': '% RH',
    },
    'cpu-temperature': {
        'title': 'cpu temperature',
        'columns': ('cpu_temperature_c',),
        'unit': '°C',
    },
}


def read_environmental(database_url, start, end, columns):
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        connection.read_only = True
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '30s'")
            cursor.execute(sql.SQL("""
                SELECT added, {} FROM public.environmental
                WHERE added >= %s AND added <= %s
                ORDER BY added ASC
            """).format(sql.SQL(', ').join(map(sql.Identifier, columns))), (start, end))
            return cursor.fetchall()


def build_environmental_figure(rows, start, end, specification):
    timestamps = [row[0].astimezone(timezone.utc).isoformat() for row in rows]
    figure = go.Figure()
    for index, (column, color) in enumerate(zip(specification['columns'], ('#88c7ff', '#f3b875')), start=1):
        figure.add_trace(go.Scatter(
            x=timestamps,
            y=[float(row[index]) if row[index] is not None else None for row in rows],
            name=column,
            yaxis='y' if index == 1 else 'y2',
            mode='lines+markers',
            line={'color': color, 'width': 2},
            marker={'size': 4},
            hovertemplate=f"%{{y}} {specification['unit']}<extra>{column}</extra>",
            connectgaps=False,
        ))
    figure.update_layout(
        chart_layout(specification['title'], start, end),
        yaxis_title=specification['unit'],
        meta={'row_count': len(rows)},
    )
    if len(specification['columns']) > 1:
        internal, external = specification['columns']
        unit = specification['unit']
        figure.update_layout(
            margin={'r': 90},
            yaxis={'title': {'text': f'{internal} ({unit})', 'font': {'color': '#88c7ff'}},
                   'tickfont': {'color': '#88c7ff'}, 'side': 'left'},
            yaxis2={'title': {'text': f'{external} ({unit})', 'font': {'color': '#f3b875'}},
                    'tickfont': {'color': '#f3b875'}, 'overlaying': 'y', 'side': 'right',
                    'showgrid': False, 'zeroline': False},
        )
    add_y_padding(figure)
    return figure
