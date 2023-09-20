import os
import psycopg2
import simplekml
from lib import log
from lib import common

conn = psycopg2.connect(os.environ['POSTGRES_URL'])
masked_postgres_url = common.mask_postgres_url_password(
    os.environ['POSTGRES_URL'])

log.debug(f'connected to PostgreSQL ({masked_postgres_url})')

cursor = conn.cursor()
cursor.execute("SELECT coordinates[0] AS longitude, \
                       coordinates[1] AS latitude, \
                       altitude_m, \
                       speed_kn, \
                       course_d, \
                       direction, \
                       added \
                FROM location ORDER BY added ASC;")

rows = cursor.fetchall()
cursor.close()
conn.close()
log.debug('closed PostgreSQL connection')

kml = simplekml.Kml()
ls = kml.newlinestring(name='StratoPi')
ls.coords = []
ls.extrude = 1
ls.altitudemode = simplekml.AltitudeMode.relativetoground
ls.style.linestyle.width = 5
ls.style.linestyle.color = simplekml.Color.blue
ls.description = ''
ls.timestamp.when = ''

for row in rows:
    longitude, latitude, altitude_m, speed_kn, course_d, direction, added = row
    ls.coords.addcoordinates([(longitude, latitude, altitude_m)])

kml.save('stratopi-location.kml')

log.info('successfully created stratopi-location.kml')
