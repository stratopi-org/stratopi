"""Shared layout for the Charts Plotly charts."""

from math import isfinite


def add_y_padding(figure):
    """Give each Y axis at least 10% headroom using Plotly's autorange."""
    values_by_axis = {}
    for trace in figure.data:
        values = [float(value) for value in trace.y
                  if value is not None and isfinite(value)]
        values_by_axis.setdefault(trace.yaxis or 'y', []).extend(values)
    for axis, values in values_by_axis.items():
        if not values:
            continue
        minimum, maximum = min(values), max(values)
        # Constant readings still need room, including when the only value is zero.
        span = maximum - minimum or abs(minimum) or 1
        padding = span * 0.1
        figure.update_layout({
            'yaxis' + axis[1:]: {
                'autorange': True,
                'autorangeoptions': {'include': [minimum - padding, maximum + padding]},
            },
        })


def chart_layout(title, start, end):
    return {
        'template': 'plotly_dark',
        'title': {'text': title, 'x': 0.03, 'font': {'size': 18}},
        'paper_bgcolor': '#161e29',
        'plot_bgcolor': '#161e29',
        'font': {'color': '#e6edf5', 'family': 'system-ui, sans-serif'},
        'margin': {'t': 65, 'r': 24, 'b': 70, 'l': 65},
        'height': 420,
        'hovermode': 'x unified',
        'legend': {'orientation': 'h', 'y': 1.08, 'x': 1, 'xanchor': 'right'},
        'xaxis': {'title': 'added', 'type': 'date',
                  'range': [start.isoformat(), end.isoformat()],
                  'gridcolor': '#2b3747', 'zeroline': False},
        'yaxis': {'gridcolor': '#2b3747', 'zeroline': False},
    }
