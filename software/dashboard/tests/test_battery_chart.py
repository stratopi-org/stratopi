import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from battery_chart import read_battery
import psycopg


class BatteryChartTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, POSTGRES_URL='postgresql://test')
        self.client = self.app.test_client()
        self.params = {'start': '2026-11-19T12:00:00Z', 'end': '2026-11-19T15:00:00Z'}

    def test_shared_timestamps_two_numeric_traces_and_requested_axis_range(self):
        timestamp = datetime(2026, 11, 19, 13, tzinfo=timezone.utc)
        with patch('app.read_battery', return_value=[(timestamp, Decimal('87.4'), 25)]) as read:
            response = self.client.get('/api/charts/battery', query_string=self.params)
        self.assertEqual(response.status_code, 200)
        figure = response.get_json()
        self.assertEqual(figure['layout']['title']['text'], 'battery')
        self.assertEqual([trace['name'] for trace in figure['data']], ['percent', 'temperature_c'])
        self.assertEqual(figure['data'][0]['x'], figure['data'][1]['x'])
        self.assertEqual(figure['data'][0]['x'], [timestamp.isoformat()])
        self.assertEqual(figure['data'][0]['y'], [87.4])
        self.assertEqual(figure['data'][1]['y'], [25.0])
        self.assertEqual(figure['data'][0]['yaxis'], 'y')
        self.assertEqual(figure['data'][1]['yaxis'], 'y2')
        self.assertEqual(figure['layout']['yaxis']['side'], 'left')
        self.assertEqual(figure['layout']['yaxis2']['side'], 'right')
        self.assertEqual(figure['layout']['yaxis2']['overlaying'], 'y')
        self.assertEqual(figure['layout']['xaxis']['range'],
                         ['2026-11-19T12:00:00+00:00', '2026-11-19T15:00:00+00:00'])
        self.assertEqual(read.call_args.args[1].hour, 12)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_empty_range_returns_valid_empty_figure(self):
        with patch('app.read_battery', return_value=[]):
            response = self.client.get('/api/charts/battery', query_string=self.params)
        self.assertEqual(response.status_code, 200)
        figure = response.get_json()
        self.assertEqual(figure['layout']['meta']['row_count'], 0)
        self.assertEqual(figure['data'][0]['x'], [])

    def test_invalid_ranges_are_rejected_before_querying(self):
        for params in [{}, {'start': 'bad', 'end': 'bad'},
                       {'start': '2026-11-19T12:00:00', 'end': '2026-11-19T15:00:00'},
                       {'start': self.params['end'], 'end': self.params['start']}]:
            with self.subTest(params=params), patch('app.read_battery') as read:
                response = self.client.get('/api/charts/battery', query_string=params)
                self.assertEqual(response.status_code, 400)
                read.assert_not_called()

    def test_database_failure_does_not_expose_credentials(self):
        with patch('app.read_battery', side_effect=psycopg.OperationalError('secret')):
            response = self.client.get('/api/charts/battery', query_string=self.params)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.get_data(as_text=True))

    def test_query_filters_in_postgresql_with_bound_dates(self):
        start = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
        end = datetime(2026, 11, 19, 15, tzinfo=timezone.utc)
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []
        with patch('battery_chart.psycopg.connect') as connect:
            connect.return_value.__enter__.return_value = connection
            self.assertEqual(read_battery('postgresql://test', start, end), [])
        self.assertTrue(connection.read_only)
        query, params = cursor.execute.call_args.args
        self.assertIn('WHERE added >= %s AND added <= %s', query)
        self.assertIn('ORDER BY added ASC', query)
        self.assertEqual(params, (start, end))
