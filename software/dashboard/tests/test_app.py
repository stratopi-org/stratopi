import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app, read_tables, page_key
import psycopg


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, POSTGRES_URL='postgresql://test')
        self.client = self.app.test_client()

    def test_headers_empty_tables_null_and_html_escaping(self):
        tables = [
            dict(schema='public', name='sensors', columns=['value', 'note'],
                 rows=[(None, '<script>alert(1)</script>')]),
            dict(schema='public', name='empty', columns=['id'], rows=[]),
        ]
        with patch('app.read_tables', return_value=tables):
            response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('<th scope="col">value</th>', html)
        self.assertIn('<th scope="col" class="id-column">id</th>', html)
        self.assertIn('NULL', html)
        self.assertIn('No rows in table.', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', html)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_missing_configuration(self):
        self.app.config['POSTGRES_URL'] = None
        self.assertEqual(self.client.get('/').status_code, 503)

    def test_coordinates_link_uses_latitude_then_longitude(self):
        tables = [dict(schema='public', name='location', columns=['coordinates', 'other'],
                       rows=[('(-87.6298,41.8781)', '(-87.6298,41.8781)'),
                             (None, None), ('<invalid>', 'plain')])]
        with patch('app.read_tables', return_value=tables):
            html = self.client.get('/').get_data(as_text=True)
        self.assertIn('href="https://www.google.com/maps/search/?api=1&amp;query=41.8781,-87.6298"', html)
        self.assertIn('<td><a href="https://www.google.com/maps/search/', html)
        self.assertIn('>(-87.6298,41.8781)</a></td>', html)
        self.assertEqual(html.count('https://www.google.com/maps/search/'), 1)
        self.assertIn('target="_blank" rel="noopener noreferrer"', html)
        self.assertIn('&lt;invalid&gt;', html)
        self.assertIn('NULL', html)
        formatter = self.app.jinja_env.filters['maps_url']
        for invalid in ['(1,2,3)', '(181,30)', '(40,91)', '(NaN,20)', '(inf,20)', 'invalid', None]:
            with self.subTest(value=invalid):
                self.assertIsNone(formatter(invalid))
        self.assertEqual(formatter((0, 0)),
                         'https://www.google.com/maps/search/?api=1&query=0.0,0.0')

    def test_id_icons_preserve_full_value_and_escape_attributes(self):
        value = '12345678-1234-1234-1234-123456789abc'
        tables = [dict(schema='public', name='sensors', columns=['id'],
                       rows=[(value,), ('"<unsafe>',), (None,)])]
        with patch('app.read_tables', return_value=tables):
            html = self.client.get('/').get_data(as_text=True)
        self.assertIn(f'data-id="{value}"', html)
        self.assertNotIn(f'>{value}</td>', html)
        self.assertIn('data-id="&#34;&lt;unsafe&gt;"', html)
        self.assertEqual(html.count('class="id-trigger"'), 2)
        self.assertIn('aria-describedby="id-popover"', html)
        self.assertIn('role="tooltip" hidden', html)
        self.assertIn('NULL', html)

    def test_added_timestamp_format(self):
        timestamp = datetime(2026, 11, 4, 22, 17, 41, tzinfo=timezone.utc)
        tables = [dict(schema='public', name='sensors',
                       columns=['added', 'other_timestamp'],
                       rows=[(timestamp, timestamp), (None, None)])]
        with patch('app.read_tables', return_value=tables):
            html = self.client.get('/').get_data(as_text=True)
        self.assertIn('<td>Nov 4 10:17:41 PM</td>', html)
        self.assertIn(str(timestamp), html)
        self.assertIn('NULL', html)
        formatter = self.app.jinja_env.filters['format_cell']
        self.assertEqual(formatter(datetime(2026, 11, 4), 'added'),
                         'Nov 4 12:00:00 AM')
        self.assertEqual(formatter(datetime(2026, 11, 4, 20, 55, 56), 'added'),
                         'Nov 4 8:55:56 PM')

    def test_database_errors_do_not_expose_secrets(self):
        with patch('app.read_tables', side_effect=psycopg.OperationalError('secret-password')):
            response = self.client.get('/')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret-password', response.get_data(as_text=True))

    def test_discovers_tables_and_quotes_identifiers(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.side_effect = [[('odd schema', 'a"table')], [('added',)], [(42,)]]
        cursor.fetchone.return_value = (1,)
        cursor.description = [SimpleNamespace(name='value')]
        with patch('app.psycopg.connect') as connect:
            connect.return_value.__enter__.return_value = connection
            tables = read_tables('postgresql://test')
        self.assertTrue(connection.read_only)
        query = cursor.execute.call_args.args[0].as_string()
        self.assertEqual(query, 'SELECT * FROM "odd schema"."a""table" ORDER BY "added" ASC, tableoid, ctid LIMIT %s OFFSET %s')
        self.assertEqual(cursor.execute.call_args.args[1], (30, 0))
        self.assertEqual(tables[0]['columns'], ['value'])
        self.assertEqual(tables[0]['rows'], [(42,)])

    def test_page_offsets_and_invalid_pages(self):
        for requested, total, expected_page, expected_count in [
            ('2', 61, 2, 3), ('3', 61, 3, 3), ('999', 61, 3, 3),
            ('bad', 61, 1, 3), ('-5', 61, 1, 3), ('2', 0, 1, 1),
            ('2', 30, 1, 1), ('2', 31, 2, 2),
        ]:
            with self.subTest(requested=requested, total=total):
                connection = MagicMock()
                cursor = connection.cursor.return_value.__enter__.return_value
                cursor.fetchall.side_effect = [[('public', 'sensors')], [], []]
                cursor.fetchone.return_value = (total,)
                cursor.description = [SimpleNamespace(name='id')]
                with patch('app.psycopg.connect') as connect:
                    connect.return_value.__enter__.return_value = connection
                    table = read_tables('postgresql://test',
                                        {page_key('public', 'sensors'): requested})[0]
                self.assertEqual(table['page'], expected_page)
                self.assertEqual(table['page_count'], expected_count)
                self.assertEqual(table['total'], total)
                self.assertEqual(table['row_start'], (expected_page - 1) * 30 + 1 if total else 0)
                self.assertEqual(table['row_end'], min(expected_page * 30, total))
                self.assertEqual(cursor.execute.call_args.args[1],
                                 (30, (expected_page - 1) * 30))
                self.assertIn('ORDER BY tableoid, ctid', cursor.execute.call_args.args[0].as_string())

    def test_table_pagination_preserves_other_pages(self):
        tables = [dict(schema='public', name=name, columns=['id'], rows=[],
                       page=page, page_count=count, total=total,
                       row_start=(page - 1) * 30 + 1 if total else 0,
                       row_end=min(page * 30, total))
                  for name, page, count, total in [('first', 2, 3, 61), ('second', 1, 1, 0)]]
        params = {page_key('public', 'first'): '2', page_key('public', 'second'): '1'}
        with patch('app.read_tables', return_value=tables):
            response = self.client.get('/', query_string=params)
        self.assertEqual(response.status_code, 200)

        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.pages = {}

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'a' and attrs.get('rel') in ('prev', 'next'):
                    self.pages[attrs['rel']] = urlsplit(attrs['href'])

        links = Links()
        html = response.get_data(as_text=True)
        links.feed(html)
        for direction, page in [('prev', '1'), ('next', '3')]:
            parsed = links.pages[direction]
            self.assertEqual(parse_qs(parsed.query),
                             {page_key('public', 'first'): [page],
                              page_key('public', 'second'): ['1']})
            self.assertEqual(parsed.fragment, 'table-1')
        self.assertIn('Page <strong>2</strong> of 3. Row 31 - 60.', html)
        self.assertNotIn('Page 1 of 1', html)
        self.assertNotIn('aria-label="second pagination"', html)
        self.assertEqual(html.count('class="pagination"'), 1)
        self.assertEqual(html.count('aria-disabled="true"'), 0)


if __name__ == '__main__':
    unittest.main()
