"""Read-only HTML browser for the configured PostgreSQL database."""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import psycopg
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, url_for
from plotly.offline import get_plotlyjs
from psycopg import sql

from battery_chart import build_battery_figure, read_battery
from database import read_connection
from environmental_charts import ENVIRONMENTAL_CHARTS, build_environmental_figure, read_environmental
from location_chart import build_location_figure, read_location
from location_map import read_location_points

load_dotenv(Path(__file__).with_name('.env'))


PAGE_SIZE = 30


def chart_time_range(args):
    start = datetime.fromisoformat(args.get('start', ''))
    end = datetime.fromisoformat(args.get('end', ''))
    if start.tzinfo is None or end.tzinfo is None or start > end:
        raise ValueError
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def page_key(schema, name):
    return 'page:' + json.dumps([schema, name], separators=(',', ':'))


def read_time_bounds(database_url):
    """Find the available time window across timestamp-based user tables."""
    bounds = []
    with read_connection(database_url) as connection:
        connection.read_only = True
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '30s'")
            cursor.execute("""
                SELECT c.table_schema, c.table_name
                FROM information_schema.columns c
                JOIN information_schema.tables t
                  ON t.table_schema = c.table_schema AND t.table_name = c.table_name
                WHERE c.column_name = 'added'
                  AND c.data_type IN ('timestamp with time zone', 'timestamp without time zone')
                  AND t.table_type = 'BASE TABLE'
                  AND c.table_schema <> 'information_schema'
                  AND c.table_schema NOT LIKE 'pg_%'
                ORDER BY c.table_schema, c.table_name
            """)
            names = cursor.fetchall()
            for schema, name in names:
                cursor.execute(sql.SQL("""
                    SELECT EXTRACT(EPOCH FROM min(added)::timestamptz),
                           EXTRACT(EPOCH FROM max(added)::timestamptz)
                    FROM {} WHERE isfinite(added)
                """).format(sql.Identifier(schema, name)))
                earliest, latest = cursor.fetchone()
                if earliest is not None:
                    bounds.append((int(earliest * 1000), int(latest * 1000)))
    if not bounds:
        return None
    return {'start': min(start for start, end in bounds),
            'end': max(end for start, end in bounds)}


def read_tables(database_url, pages=None):
    pages = pages or {}
    tables = []
    with read_connection(database_url) as connection:
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
    app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', '')

    @app.get('/assets/plotly.min.js')
    def plotly_js():
        return app.response_class(get_plotlyjs(), mimetype='application/javascript')

    @app.get('/api/charts/battery')
    def battery_chart():
        try:
            start, end = chart_time_range(request.args)
        except ValueError:
            return jsonify(error='Provide a valid start and end time with timezones, in chronological order.'), 400
        database_url = app.config['POSTGRES_URL']
        if not database_url:
            return jsonify(error='Configure POSTGRES_URL to load battery data.'), 503
        try:
            rows = read_battery(database_url, start, end)
        except psycopg.Error:
            app.logger.error('Unable to read battery chart data.')
            return jsonify(error='Unable to load battery data. Check the database connection and permissions.'), 503
        figure = build_battery_figure(rows, start, end)
        return app.response_class(figure.to_json(), mimetype='application/json')

    @app.get('/api/charts/time-bounds')
    def charts_time_bounds():
        database_url = app.config['POSTGRES_URL']
        if not database_url:
            return jsonify(error='Configure POSTGRES_URL to load the time range.'), 503
        try:
            return jsonify(read_time_bounds(database_url))
        except psycopg.Error:
            app.logger.error('Unable to refresh the available PostgreSQL time range.')
            return jsonify(error='Unable to refresh the available time range.'), 503

    @app.get('/api/charts/location/altitude')
    def location_chart():
        try:
            start, end = chart_time_range(request.args)
        except ValueError:
            return jsonify(error='Provide a valid start and end time with timezones, in chronological order.'), 400
        database_url = app.config['POSTGRES_URL']
        if not database_url:
            return jsonify(error='Configure POSTGRES_URL to load location data.'), 503
        try:
            rows = read_location(database_url, start, end)
        except psycopg.Error:
            app.logger.error('Unable to read location chart data.')
            return jsonify(error='Unable to load location data. Check the database connection and permissions.'), 503
        figure = build_location_figure(rows, start, end)
        return app.response_class(figure.to_json(), mimetype='application/json')

    @app.get('/api/charts/location/map')
    def location_map():
        try:
            start, end = chart_time_range(request.args)
        except ValueError:
            return jsonify(error='Provide a valid start and end time with timezones, in chronological order.'), 400
        database_url = app.config['POSTGRES_URL']
        if not database_url:
            return jsonify(error='Configure POSTGRES_URL to load location data.'), 503
        try:
            return jsonify(read_location_points(database_url, start, end))
        except psycopg.Error:
            app.logger.error('Unable to read location map data.')
            return jsonify(error='Unable to load location map data. Check the database connection and permissions.'), 503

    @app.get('/api/charts/environmental/<chart>')
    def environmental_chart(chart):
        specification = ENVIRONMENTAL_CHARTS.get(chart)
        if specification is None:
            return jsonify(error='Unknown environmental chart.'), 404
        try:
            start, end = chart_time_range(request.args)
        except ValueError:
            return jsonify(error='Provide a valid start and end time with timezones, in chronological order.'), 400
        database_url = app.config['POSTGRES_URL']
        if not database_url:
            return jsonify(error='Configure POSTGRES_URL to load environmental data.'), 503
        try:
            rows = read_environmental(database_url, start, end, specification['columns'])
        except psycopg.Error:
            app.logger.error('Unable to read environmental chart data.')
            return jsonify(error='Unable to load environmental data. Check the database connection and permissions.'), 503
        figure = build_environmental_figure(rows, start, end, specification)
        return app.response_class(figure.to_json(), mimetype='application/json')

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
    def charts():
        bounds = None
        error = None
        database_url = app.config['POSTGRES_URL']
        if not database_url:
            error = 'Set POSTGRES_URL in .env to load the available time range.'
        else:
            try:
                bounds = read_time_bounds(database_url)
            except psycopg.Error:
                app.logger.error('Unable to read the available PostgreSQL time range.')
                error = 'Unable to load the time range. Check the database connection and permissions.'
        return render_template('charts.html', time_bounds=bounds, error=error)

    @app.get('/data')
    def data():
        database_url = app.config['POSTGRES_URL']
        if not database_url:
            return render_template(
                'data.html', tables=[],
                error='Set POSTGRES_URL in .env to connect to the database.'
            ), 503
        try:
            tables = read_tables(database_url, request.args)
        except psycopg.Error:
            # Avoid exposing connection credentials or database contents in errors.
            app.logger.error('Unable to read PostgreSQL tables.')
            return render_template(
                'data.html', tables=[],
                error='Unable to read the database. Check the connection, permissions, and database availability.'
            ), 503
        for number, table in enumerate(tables, start=1):
            key = page_key(table['schema'], table['name'])
            page = table.get('page', 1)
            count = table.get('page_count', 1)
            for direction, target in [('previous', page - 1), ('next', page + 1)]:
                params = request.args.to_dict()
                params[key] = target
                table[f'{direction}_url'] = (
                    url_for('data') + '?' + urlencode(params) + f'#table-{number}'
                    if 1 <= target <= count else None
                )
        return render_template('data.html', tables=tables, error=None)

    @app.after_request
    def disable_cache(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500)
