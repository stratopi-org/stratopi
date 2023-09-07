import argparse
import os
import asyncio
import psycopg2
import sys
import signal
import time
import pprint
from lib import log
from lib import common
from lib import gps

signal.signal(signal.SIGINT, lambda sig, frame: (gps.power_off(), sys.exit(0)))

NAME = 'location'
SLEEP_TIME = 60 * 1  # 1 minute

try:
    with open('.version', 'r', encoding='UTF-8') as f:
        VERSION = f.read().strip()
except FileNotFoundError as err:
    log.error(err, exit_code=3)

parser = argparse.ArgumentParser(prog=NAME)
parser.add_argument('--version',
                    action='version',
                    version=f'{NAME} v{VERSION} ({common.python_version()})',
                    help='show version and exit')

parser.parse_args()

log.info(f'{NAME} v{VERSION} ({common.python_version()})')
log.info(f'refreshing location data every {common.sec_to_min(SLEEP_TIME)} minute(s)')

gps.power_on()


async def loop_fn():
    while True:
        conn = psycopg2.connect(os.environ['POSTGRES_URL'])
        masked_postgres_url = common.mask_postgres_url_password(
            os.environ['POSTGRES_URL'])
        log.debug(f'connected to PostgreSQL ({masked_postgres_url})')

        cursor = conn.cursor()

        try:
            gps_response = gps.parse(gps.get())

            cursor.execute('INSERT INTO location (date, time, coordinates, altitude_m, speed_mps, course_d, direction) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                            (gps_response['date'], gps_response['time'],
                             POINT(gps_response['latitude'], gps_response['lontitude']),
                             gps_response['altitude_m'], gps_response['speed_mps'],
                             gps_response['course_d'], gps_response['direction']))

            conn.commit()
            log.info(
                 f"inserted location data ({gps_response['latitude']}, {gps_response['lontitude']}, {gps_response['altitude_m']}) into PostgreSQL")
        except Exception as err:
            log.error(err)
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            log.debug('closed PostgreSQL connection')

        await asyncio.sleep(SLEEP_TIME)

asyncio.run(loop_fn())
