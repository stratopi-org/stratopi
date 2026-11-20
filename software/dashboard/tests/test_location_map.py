import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from location_map import read_location_points


class LocationMapTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, POSTGRES_URL='postgresql://test', GOOGLE_MAPS_API_KEY='')
        self.client = self.app.test_client()
        self.params = {'start': '2026-11-19T12:00:00Z', 'end': '2026-11-19T15:00:00Z'}

    def test_geojson_uses_longitude_latitude_and_preserves_each_record(self):
        start = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
        end = datetime(2026, 11, 19, 15, tzinfo=timezone.utc)
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ('one', start, -87.6, 41.8, Decimal('150.2'), None, Decimal('4.2'), 90, 'E'),
            ('two', end, -87.6, 41.8, Decimal('151.2'), Decimal('2'), 0, 0, 'N'),
        ]
        with patch('location_map.read_connection') as connect:
            connect.return_value.__enter__.return_value = connection
            result = read_location_points('postgresql://test', start, end)
        self.assertEqual(result['type'], 'FeatureCollection')
        self.assertEqual(len(result['features']), 2)
        first = result['features'][0]
        self.assertEqual(first['geometry'], {'type': 'Point', 'coordinates': [-87.6, 41.8]})
        self.assertEqual(first['properties']['altitude_m'], 150.2)
        self.assertIsNone(first['properties']['vertical_speed_mpm'])
        self.assertEqual(first['properties']['added'], start.isoformat())
        self.assertEqual([item['id'] for item in result['features']], ['one', 'two'])
        query, params = cursor.execute.call_args.args
        self.assertIn('WHERE added >= %s AND added <= %s', query)
        self.assertIn('coordinates[0] BETWEEN -180 AND 180', query)
        self.assertIn('coordinates[1] BETWEEN -90 AND 90', query)
        self.assertNotIn('LIMIT', query)
        self.assertEqual(params, (start, end))

    def test_endpoint_empty_data_validation_and_database_errors(self):
        url = '/api/charts/location/map'
        with patch('app.read_location_points', return_value={'type': 'FeatureCollection', 'features': []}) as read:
            response = self.client.get(url, query_string=self.params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['features'], [])
        self.assertEqual(read.call_args.args[1].hour, 12)
        self.assertEqual(read.call_args.args[2].hour, 15)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        with patch('app.read_location_points') as read:
            self.assertEqual(self.client.get(url).status_code, 400)
            read.assert_not_called()
        with patch('app.read_location_points', side_effect=psycopg.OperationalError('secret')):
            response = self.client.get(url, query_string=self.params)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.get_data(as_text=True))

    def test_panel_follows_altitude_and_explains_missing_api_key(self):
        with patch('app.read_time_bounds', return_value={'start': 1000, 'end': 2000}):
            html = self.client.get('/').get_data(as_text=True)
        self.assertLess(html.index('data-chart-url="/api/charts/location/altitude"'),
                        html.index('id="location-map-panel"'))
        self.assertIn('Set GOOGLE_MAPS_API_KEY', html)
        self.assertIn('/api/charts/location/map', html)
        self.assertLess(html.index('/static/location-map.js'), html.index('/static/charts.js'))
