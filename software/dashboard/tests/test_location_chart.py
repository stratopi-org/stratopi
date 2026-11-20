import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from location_chart import read_location


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
        self.assertEqual(trace['marker']['symbol'], ['arrow-down', 'circle'])
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
        rows = [(timestamp, 140, speed, 0, 0, 'N')
                for speed in [Decimal('3.1'), Decimal('-2.5'), Decimal('0'), None]]
        with patch('app.read_location', return_value=rows):
            response = self.client.get('/api/charts/location/altitude', query_string=self.params)
        marker = response.get_json()['data'][0]['marker']
        self.assertEqual(marker['symbol'], ['arrow-up', 'arrow-down', 'circle', 'circle'])
        self.assertEqual(marker['color'], ['#86dba0', '#f38b91', '#a3b1c2', '#a3b1c2'])
        self.assertEqual(marker['size'], [10, 10, 4, 4])

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
