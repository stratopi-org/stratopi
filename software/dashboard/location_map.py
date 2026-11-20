"""GeoJSON location readings for the shared Charts time range."""

from datetime import timezone
from math import isfinite

from database import read_connection


def read_location_points(database_url, start, end):
    with read_connection(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '30s'")
            cursor.execute("""
                SELECT id, added, coordinates[0] AS longitude, coordinates[1] AS latitude,
                       altitude_m, vertical_speed_mpm, speed_kn, course_d, direction
                FROM public.location
                WHERE added >= %s AND added <= %s
                  AND coordinates[0] BETWEEN -180 AND 180
                  AND coordinates[1] BETWEEN -90 AND 90
                ORDER BY added ASC
            """, (start, end))
            rows = cursor.fetchall()
    features = []
    for row in rows:
        properties = {'added': row[1].astimezone(timezone.utc).isoformat()}
        for index, name in enumerate(('altitude_m', 'vertical_speed_mpm', 'speed_kn', 'course_d'), start=4):
            value = float(row[index]) if row[index] is not None else None
            properties[name] = value if value is not None and isfinite(value) else None
        properties['direction'] = str(row[8]) if row[8] is not None else None
        features.append({
            'type': 'Feature', 'id': str(row[0]),
            'geometry': {'type': 'Point', 'coordinates': [float(row[2]), float(row[3])]},
            'properties': properties,
        })
    return {'type': 'FeatureCollection', 'features': features}
