"""Read-only HTML browser for the configured PostgreSQL database."""

import os
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import psycopg
from dotenv import load_dotenv
from flask import Flask, render_template, request, url_for
from psycopg import sql

load_dotenv(Path(__file__).with_name('.env'))


PAGE_SIZE = 30


def page_key(schema, name):
    return 'page:' + json.dumps([schema, name], separators=(',', ':'))


def read_tables(database_url, pages=None):
    pages = pages or {}
    tables = []
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        connection.read_only = True
        connection.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '30s'")
            cursor.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                  AND table_schema <> 'information_schema'
                  AND table_schema NOT LIKE 'pg_%'
                ORDER BY table_schema, table_name
            """)
            names = cursor.fetchall()
            for schema, name in names:
                identifier = sql.Identifier(schema, name)
                cursor.execute(sql.SQL('SELECT count(*) FROM {}').format(identifier))
                total = cursor.fetchone()[0]
                page_count = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
                try:
                    page = int(pages.get(page_key(schema, name), 1))
                except (ValueError, TypeError):
                    page = 1
                page = max(1, min(page, page_count))
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                      AND column_name = 'added'
                """, (schema, name))
                has_added = bool(cursor.fetchall())
                # Physical location breaks timestamp ties without sorting by UUID.
                order = sql.SQL('"added" ASC, tableoid, ctid') if has_added else sql.SQL('tableoid, ctid')
                cursor.execute(
                    sql.SQL('SELECT * FROM {} ORDER BY {} LIMIT %s OFFSET %s').format(identifier, order),
                    (PAGE_SIZE, (page - 1) * PAGE_SIZE),
                )
                tables.append({
                    'schema': schema,
                    'name': name,
                    'columns': [column.name for column in cursor.description],
                    'rows': cursor.fetchall(),
                    'total': total,
                    'page': page,
                    'page_count': page_count,
                    'row_start': (page - 1) * PAGE_SIZE + 1 if total else 0,
                    'row_end': min(page * PAGE_SIZE, total),
                })
    return tables


def create_app():
    app = Flask(__name__)
    app.config['POSTGRES_URL'] = os.environ.get('POSTGRES_URL')

    @app.template_filter('direction_angle')
    def direction_angle(value):
        if not isinstance(value, str):
            return None
        return {'N': 0, 'NE': 45, 'E': 90, 'SE': 135,
                'S': 180, 'SW': 225, 'W': 270, 'NW': 315}.get(value.strip().upper())

    @app.template_filter('maps_url')
    def maps_url(value):
        # PostgreSQL POINT values use (x, y): longitude, latitude.
        try:
            parts = value.strip().removeprefix('(').removesuffix(')').split(',') if isinstance(value, str) else value
            longitude, latitude = map(float, parts)
        except (TypeError, ValueError, OverflowError):
            return None
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return None
        return f'https://www.google.com/maps/search/?api=1&query={latitude},{longitude}'

    @app.template_filter('format_cell')
    def format_cell(value, column):
        if column == 'added' and isinstance(value, datetime):
            return f'{value:%b} {value.day} {value.hour % 12 or 12}:{value:%M:%S %p}'
        return value

    @app.get('/')
    def index():
        database_url = app.config['POSTGRES_URL']
        if not database_url:
            return render_template(
                'index.html', tables=[],
                error='Set POSTGRES_URL in dashboard/.env to connect to your database.'
            ), 503
        try:
            tables = read_tables(database_url, request.args)
        except psycopg.Error:
            # Avoid exposing connection credentials or database contents in errors.
            app.logger.error('Unable to read PostgreSQL tables.')
            return render_template(
                'index.html', tables=[],
                error='Unable to read the database. Check the connection, table permissions, and database availability.'
            ), 503
        for number, table in enumerate(tables, start=1):
            key = page_key(table['schema'], table['name'])
            page = table.get('page', 1)
            count = table.get('page_count', 1)
            for direction, target in [('previous', page - 1), ('next', page + 1)]:
                params = request.args.to_dict()
                params[key] = target
                table[f'{direction}_url'] = (
                    url_for('index') + '?' + urlencode(params) + f'#table-{number}'
                    if 1 <= target <= count else None
                )
        return render_template('index.html', tables=tables, error=None)

    @app.after_request
    def disable_cache(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
