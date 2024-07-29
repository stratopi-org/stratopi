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
cursor.execute("SELECT (date + time)::TIMESTAMP AS timestamp, \
                       FORMAT('%sT%sZ', TO_CHAR(date, 'YYYY-MM-DD'), TO_CHAR(time, 'HH24:MI:SS')) AS timestamp_iso_8601, \
                       coordinates[0] AS longitude, \
                       coordinates[1] AS latitude, \
                       altitude_m, \
                       speed_kn, \
                       course_d, \
                       direction \
                FROM location ORDER BY timestamp ASC;")

rows = cursor.fetchall()
cursor.close()
conn.close()
log.debug('closed PostgreSQL connection')

kml = simplekml.Kml()
ls = kml.newlinestring(name='StratoPi')
ls.coords = []
ls.extrude = 1
ls.altitudemode = simplekml.AltitudeMode.absolute
ls.style.linestyle.width = 7
ls.style.linestyle.color = simplekml.Color.blue

for i, row in enumerate(rows, start=1):
    timestamp, timestamp_iso_8601, longitude, latitude, altitude_m, speed_kn, course_d, direction = row
    pnt = kml.newpoint(name=f'#{i}', coords=[(longitude, latitude, altitude_m)])  # coords order is (longitude, latitude, altitude)
    pnt.timestamp.when = timestamp_iso_8601
    pnt.description = f'Date and time: {timestamp_iso_8601}\nAltitude: {altitude_m}m / {common.meters_to_feet(altitude_m)}ft\nSpeed: {speed_kn}kn / {common.knots_to_mps(speed_kn)}m/s / {common.knots_to_mph(speed_kn)}mph\nCourse: {course_d}°\nDirection: {direction}'
    pnt.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/paddle/red-circle.png'
    ls.coords.addcoordinates([(longitude, latitude, altitude_m)])

kml.save(kml_file)

log.info(f"successfully created kml export '{kml_file}'")
