import os
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import psycopg
from psycopg_pool import PoolTimeout

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import database
from app import create_app, read_tables, read_time_bounds
from battery_chart import read_battery
from environmental_charts import read_environmental
from location_chart import read_location


class DatabasePoolTests(unittest.TestCase):
    def tearDown(self):
        database.close_pools()

    def test_concurrent_callers_create_only_one_lazy_bounded_pool(self):
        with patch('database.ConnectionPool') as factory:
            with ThreadPoolExecutor(max_workers=8) as executor:
                pools = list(executor.map(database.get_pool, ['postgresql://test'] * 20))
            factory.assert_called_once()
            pool = factory.return_value
            self.assertTrue(all(item is pool for item in pools))
            pool.open.assert_called_once()
            options = factory.call_args.kwargs
            self.assertEqual((options['min_size'], options['max_size']), (1, 2))
            self.assertEqual(options['timeout'], 5)
            self.assertFalse(options['open'])
            self.assertEqual(options['configure'], database.reset_connection)
            self.assertEqual(options['reset'], database.reset_connection)

    def test_shutdown_closes_pool_and_next_use_can_create_a_new_one(self):
        with patch('database.ConnectionPool') as factory:
            database.get_pool('postgresql://test')
            database.close_pools()
            factory.return_value.close.assert_called_once()
            database.get_pool('postgresql://test')
            self.assertEqual(factory.call_count, 2)

    def test_reset_restores_read_only_and_default_isolation(self):
        connection = MagicMock()
        connection.read_only = False
        connection.autocommit = True
        connection.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        connection.deferrable = True
        database.reset_connection(connection)
        self.assertTrue(connection.read_only)
        self.assertFalse(connection.autocommit)
        self.assertIsNone(connection.isolation_level)
        self.assertIsNone(connection.deferrable)

    def test_exhausted_pool_uses_existing_database_error_responses(self):
        app = create_app()
        app.config.update(TESTING=True, POSTGRES_URL='postgresql://test')
        params = {'start': '2026-11-19T12:00:00Z', 'end': '2026-11-19T15:00:00Z'}
        for route in ['/data', '/api/charts/time-bounds', '/api/charts/battery',
                      '/api/charts/environmental/temperature', '/api/charts/location/altitude']:
            with self.subTest(route=route), patch('database.get_pool', side_effect=PoolTimeout('secret')):
                response = app.test_client().get(route, query_string=params)
                self.assertEqual(response.status_code, 503)
                self.assertNotIn('secret', response.get_data(as_text=True))


@unittest.skipUnless(os.environ.get('DASHBOARD_TEST_POSTGRES_URL'), 'Optional live PostgreSQL tests')
class LiveDatabasePoolTests(unittest.TestCase):
    def setUp(self):
        self.url = os.environ['DASHBOARD_TEST_POSTGRES_URL']
        database.close_pools()

    def tearDown(self):
        database.close_pools()

    def test_all_readers_reuse_the_same_bounded_pool(self):
        pool = database.get_pool(self.url)
        now = datetime.now(timezone.utc)
        for _ in range(2):
            read_time_bounds(self.url)
            read_tables(self.url)
            read_battery(self.url, now, now)
            read_environmental(self.url, now, now, ('cpu_temperature_c',))
            read_location(self.url, now, now)
        self.assertIs(database.get_pool(self.url), pool)
        self.assertLessEqual(pool.get_stats()['connections_num'], 2)

    def test_reused_connection_resets_isolation_and_rolls_back_errors(self):
        pool = database.get_pool(self.url)
        pool.resize(min_size=1, max_size=1)
        with database.read_connection(self.url) as connection:
            pid = connection.info.backend_pid
            connection.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
            default_timeout = connection.execute('SHOW statement_timeout').fetchone()[0]
            connection.execute("SET LOCAL statement_timeout = '1s'")
            self.assertEqual(connection.execute('SHOW transaction_read_only').fetchone()[0], 'on')
        with self.assertRaises(psycopg.errors.DivisionByZero):
            with database.read_connection(self.url) as connection:
                self.assertEqual(connection.info.backend_pid, pid)
                self.assertIsNone(connection.isolation_level)
                self.assertEqual(connection.execute('SHOW statement_timeout').fetchone()[0], default_timeout)
                connection.execute('SELECT 1 / 0')
        with database.read_connection(self.url) as connection:
            self.assertEqual(connection.info.backend_pid, pid)
            self.assertEqual(connection.execute('SELECT 1').fetchone(), (1,))
            self.assertEqual(connection.execute('SHOW transaction_read_only').fetchone()[0], 'on')

    def test_exhaustion_is_bounded_and_returning_connections_recovers(self):
        pool = database.get_pool(self.url)
        with database.read_connection(self.url) as first:
            with database.read_connection(self.url) as second:
                self.assertNotEqual(first.info.backend_pid, second.info.backend_pid)
                with self.assertRaises(PoolTimeout):
                    with pool.connection(timeout=0.05):
                        self.fail('A third connection must not be opened')
        with database.read_connection(self.url) as connection:
            self.assertEqual(connection.execute('SELECT 1').fetchone(), (1,))
        self.assertEqual(pool.get_stats()['pool_size'], 2)
