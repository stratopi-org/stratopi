import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from environmental_charts import read_environmental
import psycopg


class EnvironmentalChartTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, POSTGRES_URL='postgresql://test')
        self.client = self.app.test_client()
        self.params = {'start': '2026-11-19T12:00:00Z', 'end': '2026-11-19T15:00:00Z'}

    def test_all_four_charts_use_requested_columns_dates_and_units(self):
        cases = [
            ('temperature', 'temperature', ('in_temperature_c', 'ex_temperature_c'), '°C'),
            ('pressure', 'pressure', ('in_pressure_hpa', 'ex_pressure_hpa'), 'hPa'),
            ('humidity', 'humidity', ('in_humidity_rh', 'ex_humidity_rh'), '% RH'),
            ('cpu-temperature', 'cpu temperature', ('cpu_temperature_c',), '°C'),
        ]
        timestamp = datetime(2026, 11, 19, 13, tzinfo=timezone.utc)
        for chart, title, columns, unit in cases:
            with self.subTest(chart=chart):
                rows = [(timestamp, *([Decimal('24.5')] * len(columns))),
                        (timestamp, *([None] * len(columns)))]
                with patch('app.read_environmental', return_value=rows) as read:
                    response = self.client.get(f'/api/charts/environmental/{chart}', query_string=self.params)
                self.assertEqual(response.status_code, 200)
                figure = response.get_json()
                self.assertEqual(figure['layout']['title']['text'], title)
                if len(columns) == 2:
                    self.assertEqual(figure['layout']['yaxis']['title']['text'], f'{columns[0]} ({unit})')
                    self.assertEqual(figure['layout']['yaxis2']['title']['text'], f'{columns[1]} ({unit})')
                    self.assertEqual(figure['layout']['yaxis']['side'], 'left')
                    self.assertEqual(figure['layout']['yaxis2']['side'], 'right')
                    self.assertEqual(figure['layout']['yaxis2']['overlaying'], 'y')
                    self.assertEqual([trace['yaxis'] for trace in figure['data']], ['y', 'y2'])
                else:
                    self.assertEqual(figure['layout']['yaxis']['title']['text'], unit)
                    self.assertNotIn('yaxis2', figure['layout'])
                self.assertEqual([trace['name'] for trace in figure['data']], list(columns))
                for trace in figure['data']:
                    self.assertEqual(trace['x'], [timestamp.isoformat()] * 2)
                    self.assertEqual(trace['y'], [24.5, None])
                    self.assertFalse(trace['connectgaps'])
                self.assertEqual(figure['layout']['xaxis']['range'],
                                 ['2026-11-19T12:00:00+00:00', '2026-11-19T15:00:00+00:00'])
                self.assertEqual(read.call_args.args[3], columns)

    def test_empty_ranges_and_errors(self):
        url = '/api/charts/environmental/temperature'
        with patch('app.read_environmental', return_value=[]):
            response = self.client.get(url, query_string=self.params)
        self.assertEqual(response.get_json()['layout']['meta']['row_count'], 0)
        with patch('app.read_environmental') as read:
            self.assertEqual(self.client.get(url).status_code, 400)
            self.assertEqual(self.client.get('/api/charts/environmental/unknown').status_code, 404)
            read.assert_not_called()
        with patch('app.read_environmental', side_effect=psycopg.OperationalError('secret')):
            response = self.client.get(url, query_string=self.params)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.get_data(as_text=True))

    def test_query_quotes_columns_and_filters_in_postgresql(self):
        start = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
        end = datetime(2026, 11, 19, 15, tzinfo=timezone.utc)
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []
        with patch('environmental_charts.read_connection') as connect:
            connect.return_value.__enter__.return_value = connection
            read_environmental('postgresql://test', start, end, ('in_pressure_hpa', 'ex_pressure_hpa'))
        query, params = cursor.execute.call_args.args
        self.assertIn('"in_pressure_hpa", "ex_pressure_hpa"', query.as_string())
        self.assertIn('WHERE added >= %s AND added <= %s', query.as_string())
        self.assertIn('ORDER BY added ASC', query.as_string())
        self.assertEqual(params, (start, end))
        self.assertTrue(connection.read_only)
