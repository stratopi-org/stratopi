import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from battery_chart import build_battery_figure
from chart_style import add_y_padding
from environmental_charts import ENVIRONMENTAL_CHARTS, build_environmental_figure
from location_chart import build_location_figure


class ChartPaddingTests(unittest.TestCase):
    def test_each_y_axis_gets_its_own_span_padding(self):
        figure = go.Figure([
            go.Scatter(y=[20, 40], yaxis='y'),
            go.Scatter(y=[-10, 10], yaxis='y2'),
        ])
        add_y_padding(figure)
        self.assertEqual(list(figure.layout.yaxis.autorangeoptions.include), [18, 42])
        self.assertEqual(list(figure.layout.yaxis2.autorangeoptions.include), [-12, 12])
        for axis in (figure.layout.yaxis, figure.layout.yaxis2):
            self.assertTrue(axis.autorange)
            self.assertIsNone(axis.range)

    def test_shared_axis_combines_traces_and_ignores_missing_values(self):
        figure = go.Figure([go.Scatter(y=[None, 10, 20]),
                             go.Scatter(y=[30, float('nan'), float('inf')])])
        add_y_padding(figure)
        self.assertEqual(list(figure.layout.yaxis.autorangeoptions.include), [8, 32])

    def test_constant_zero_and_empty_readings(self):
        for values, expected in [([50, 50], [45, 55]), ([-50], [-55, -45]), ([0], [-0.1, 0.1])]:
            with self.subTest(values=values):
                figure = go.Figure(go.Scatter(y=values))
                add_y_padding(figure)
                self.assertEqual(list(figure.layout.yaxis.autorangeoptions.include), expected)
        figure = go.Figure(go.Scatter(y=[None]))
        add_y_padding(figure)
        self.assertIsNone(figure.layout.yaxis.autorangeoptions.include)

    def test_all_charts_chart_builders_apply_padding_without_changing_time_range(self):
        timestamp = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
        figures = [build_battery_figure([(timestamp, 80, 20), (timestamp, 90, 30)], timestamp, timestamp)]
        figures.append(build_location_figure([(timestamp, 140, None, 0, 0, 'N')], timestamp, timestamp))
        for specification in ENVIRONMENTAL_CHARTS.values():
            rows = [(timestamp, *([20] * len(specification['columns']))),
                    (timestamp, *([30] * len(specification['columns'])))]
            figures.append(build_environmental_figure(rows, timestamp, timestamp, specification))
        for figure in figures:
            with self.subTest(title=figure.layout.title.text):
                self.assertTrue(figure.layout.yaxis.autorange)
                self.assertIsNotNone(figure.layout.yaxis.autorangeoptions.include)
                if 'yaxis2' in figure.layout:
                    self.assertIsNotNone(figure.layout.yaxis2.autorangeoptions.include)
                self.assertEqual(list(figure.layout.xaxis.range), [timestamp.isoformat()] * 2)
