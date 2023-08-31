import argparse
import os
import asyncio
import psycopg2
from lib import log
from lib import common
from lib import unix_socket

NAME = 'battery'
UNIX_SOCKET_PATH = '/tmp/pisugar-server.sock'
SLEEP_TIME = 60 * 3

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
log.info(f'refreshing battery data every {common.sec_to_min(SLEEP_TIME)} minute(s)')


async def loop_fn():
    while True:
        conn = psycopg2.connect(os.environ['POSTGRES_URL'])
        masked_postgres_url = common.mask_postgres_url_password(
            os.environ['POSTGRES_URL'])
        log.debug(f'connected to PostgreSQL ({masked_postgres_url})')

        battery_percent_sc = None
        battery_temperature_sc = None
        cursor = conn.cursor()

        try:
            battery_percent_sc = unix_socket.connect(UNIX_SOCKET_PATH)
            battery_percent = unix_socket.send(battery_percent_sc, f'get battery')
            battery_percent = common.cleanup_data(battery_percent)
            unix_socket.close(battery_percent_sc)

            battery_temperature_sc = unix_socket.connect(UNIX_SOCKET_PATH)
            battery_temperature = unix_socket.send(battery_temperature_sc, f'get temperature')
            battery_temperature = common.cleanup_data(battery_temperature)
            unix_socket.close(battery_temperature_sc)

            cursor.execute('INSERT INTO battery (percent, temperature) VALUES (%s, %s)',
                           (battery_percent, battery_temperature))

            conn.commit()
            log.info(
                f'inserted battery data {battery_percent}%, {battery_temperature}°C into PostgreSQL')
        except Exception as err:
            log.error(err)
            conn.rollback()
        finally:
            unix_socket.close(battery_percent_sc)
            unix_socket.close(battery_temperature_sc)

            cursor.close()
            conn.close()
            log.debug('closed PostgreSQL connection')

        await asyncio.sleep(SLEEP_TIME)

asyncio.run(loop_fn())
