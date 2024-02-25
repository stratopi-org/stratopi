import datetime
import tempfile
import os
import psycopg2
import simplekml
from lib import log
from lib import common

conn = psycopg2.connect(os.environ['POSTGRES_URL'])
masked_postgres_url = common.mask_postgres_url_password(
    os.environ['POSTGRES_URL'])

log.debug(f'connected to PostgreSQL ({masked_postgres_url})')

now = datetime.datetime.now()
current_date = now.strftime("%Y_%m_%d_%H_%M_%S")
kml_file = os.path.join(tempfile.gettempdir(),
                        f'stratopi_location_{current_date}.kml')

cursor = conn.cursor()
cursor.execute("SELECT date, \
                       time, \
                       FORMAT('%sT%sZ', TO_CHAR(date, 'YYYY-MM-DD'), TO_CHAR(time, 'HH24:MI:SS')) AS timestamp_iso_8601 \
                       coordinates[0] AS longitude, \
                       coordinates[1] AS latitude, \
                       altitude_m, \
                       speed_kn, \
                       course_d, \
                       direction \
                FROM location ORDER BY added ASC;")

rows = cursor.fetchall()
cursor.close()
conn.close()
log.debug('closed PostgreSQL connection')

kml = simplekml.Kml()
ls = kml.newlinestring(name='StratoPi')
ls.coords = []
ls.extrude = 1
ls.altitudemode = simplekml.AltitudeMode.absolute
ls.style.linestyle.width = 6
ls.style.linestyle.color = simplekml.Color.blue

for row in rows:
    date, time, timestamp_iso_8601, longitude, latitude, altitude_m, speed_kn, course_d, direction = row
    pnt = kml.newpoint(name=f'{date} {time}', coords=[(longitude, latitude, altitude_m)])
    pnt.timestamp.when = timestamp_iso_8601
    pnt.description = f'Altitude: {altitude_m}m\nSpeed: {speed_kn}kn\nCourse: {course_d}°\nDirection: {direction}'
    pnt.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/paddle/red-circle.png'
    ls.coords.addcoordinates([(longitude, latitude, altitude_m)])

kml.save(kml_file)

log.info(f"successfully created kml export '{kml_file}'")
