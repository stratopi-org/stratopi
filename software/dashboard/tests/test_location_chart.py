import sys
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from location_chart import build_location_figure, read_location


class LocationChartTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, POSTGRES_URL='postgresql://test')
        self.client = self.app.test_client()
        self.params = {'start': '2026-11-19T12:00:00Z', 'end': '2026-11-19T15:00:00Z'}

    def test_chart_keeps_altitude_and_hover_details_aligned_per_reading(self):
        first = datetime(2026, 11, 19, 13, tzinfo=timezone.utc)
        second = datetime(2026, 11, 19, 14, tzinfo=timezone.utc)
        rows = [(first, Decimal('140.2'), Decimal('-3.1'), Decimal('5.2'), Decimal('225.0'), 'SW'),
                (second, Decimal('150.2'), None, Decimal('0.0'), Decimal('0.0'), 'N')]
        with patch('app.read_location', return_value=rows) as read:
            response = self.client.get('/api/charts/location/altitude', query_string=self.params)
        self.assertEqual(response.status_code, 200)
        figure = response.get_json()
        trace = figure['data'][0]
        self.assertEqual(figure['layout']['title']['text'], 'altitude')
        self.assertEqual(figure['layout']['yaxis']['title']['text'], 'altitude_m (m)')
        self.assertEqual(trace['x'], [first.isoformat(), second.isoformat()])
        self.assertEqual(trace['y'], [140.2, 150.2])
        self.assertEqual(trace['customdata'], [[-3.1, 5.2, 225.0, 'SW'], ['NULL', 0.0, 0.0, 'N']])
        self.assertEqual(trace['marker']['symbol'], 'circle')
        for field in ['vertical_speed_mpm', 'speed_kn', 'course_d', 'direction']:
            self.assertIn(field, trace['hovertemplate'])
        self.assertTrue(figure['layout']['yaxis']['autorange'])
        self.assertEqual(read.call_args.args[1].hour, 12)
        self.assertEqual(read.call_args.args[2].hour, 15)

    def test_empty_chart_and_error_paths(self):
        url = '/api/charts/location/altitude'
        with patch('app.read_location', return_value=[]):
            response = self.client.get(url, query_string=self.params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['data'][0]['x'], [])
        self.assertEqual(response.get_json()['layout']['meta']['row_count'], 0)
        with patch('app.read_location') as read:
            self.assertEqual(self.client.get(url).status_code, 400)
            read.assert_not_called()
        with patch('app.read_location', side_effect=psycopg.OperationalError('secret')):
            response = self.client.get(url, query_string=self.params)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.get_data(as_text=True))

    def test_ascent_descent_zero_and_missing_speed_use_matching_markers(self):
        timestamp = datetime(2026, 11, 19, 13, tzinfo=timezone.utc)
        rows = [(timestamp + timedelta(minutes=index * 20), 140, speed, 0, 0, 'N')
                for index, speed in enumerate([Decimal('3.1'), Decimal('-2.5'), Decimal('0'), None])]
        with patch('app.read_location', return_value=rows):
            response = self.client.get('/api/charts/location/altitude', query_string=self.params)
        figure = response.get_json()
        arrows = figure['layout']['annotations']
        self.assertEqual([arrow['text'] for arrow in arrows], ['↑', '↓', '↓'])
        self.assertEqual([arrow['font']['color'] for arrow in arrows], ['#86dba0', '#f38b91', '#f38b91'])
        self.assertEqual(figure['data'][0]['marker']['symbol'], 'circle')

    def test_arrow_density_tracks_selected_time_span_without_dropping_data(self):
        start = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
        rows = [(start + timedelta(seconds=index), 140 + index, index + 1, 0, 0, 'N')
                for index in range(600)]
        wide = build_location_figure(rows, start, start + timedelta(minutes=10))
        self.assertEqual(len(wide.layout.annotations), 18)
        self.assertEqual(len(wide.data[0].x), 600)
        self.assertEqual(len(wide.data[0].customdata), 600)
        # The same 10 minutes of readings occupy fewer intervals in a 3-hour view.
        broader = build_location_figure(rows, start, start + timedelta(hours=3))
        self.assertEqual(len(broader.layout.annotations), 1)
        self.assertEqual(len(broader.data[0].y), 600)

    def test_arrows_have_equal_added_spacing_with_irregular_sensor_readings(self):
        start = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
        rows = [(start + timedelta(seconds=seconds), altitude, speed, 0, 0, 'N')
                for seconds, altitude, speed in [(0, 140, 1), (100, 150, -5), (600, 160, 2)]]
        figure = build_location_figure(rows, start, start + timedelta(minutes=10))
        arrows = figure.layout.annotations
        times = [datetime.fromisoformat(arrow.x) for arrow in arrows]
        self.assertEqual(len(times), 18)
        self.assertEqual(times[0], start + timedelta(seconds=600 / 36))
        for left, right in zip(times, times[1:]):
            self.assertAlmostEqual((right - left).total_seconds(), 600 / 18, places=5)
        self.assertAlmostEqual(arrows[0].y, 140 + (600 / 36) / 10, places=5)
        self.assertEqual(arrows[0].text, '↑')
        self.assertEqual(arrows[2].text, '↓')
        self.assertEqual(len(figure.data[0].x), 3)

    def test_single_reading_zero_and_missing_speed(self):
        start = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
        for speed, count in [(1, 1), (0, 0), (None, 0)]:
            figure = build_location_figure([(start, 140, speed, 0, 0, 'N')], start, start)
            self.assertEqual(len(figure.layout.annotations), count)

    def test_query_uses_the_pool_and_filters_and_sorts_by_added(self):
        start = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
        end = datetime(2026, 11, 19, 15, tzinfo=timezone.utc)
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        with patch('location_chart.read_connection') as connect:
            connect.return_value.__enter__.return_value = connection
            read_location('postgresql://test', start, end)
        connect.assert_called_once_with('postgresql://test')
        query, params = cursor.execute.call_args.args
        self.assertIn('SELECT added, altitude_m, vertical_speed_mpm, speed_kn, course_d, direction', query)
        self.assertIn('FROM public.location', query)
        self.assertIn('WHERE added >= %s AND added <= %s', query)
        self.assertIn('ORDER BY added ASC', query)
        self.assertEqual(params, (start, end))
