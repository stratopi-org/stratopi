import argparse
import os
import asyncio
import psycopg2
import smbus2
import bme280
from lib import log
from lib import common

NAME = 'environmental'
SLEEP_TIME = 60 * 2  # 2 minutes
BME280_ADDRESS = 0x76

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
log.info(f'refreshing {NAME} data every {common.sec_to_min(SLEEP_TIME)} minute(s)')

bus = smbus2.SMBus(1)
calibration_params = bme280.load_calibration_params(bus, BME280_ADDRESS)


async def loop_fn():
    while True:
        conn = psycopg2.connect(os.environ['POSTGRES_URL'])
        masked_postgres_url = common.mask_postgres_url_password(
            os.environ['POSTGRES_URL'])
        log.debug(f'connected to PostgreSQL ({masked_postgres_url})')

        cursor = conn.cursor()

        try:
            data = bme280.sample(bus, BME280_ADDRESS, calibration_params)
            temperature = common.format_data(data.temperature)
            pressure = common.format_data(data.pressure)
            humidity = common.format_data(data.humidity)

            cursor.execute('INSERT INTO environmental (temperature_c, pressure_hpa, humidity_rh) VALUES (%s, %s, %s)',
                           (temperature, pressure, humidity))

            conn.commit()
            log.info(
                f'inserted {NAME} data {temperature}°C {pressure} hPa {humidity} %rH into PostgreSQL')
        except Exception as err:
            log.error(err)
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            log.debug('closed PostgreSQL connection')

        await asyncio.sleep(SLEEP_TIME)

asyncio.run(loop_fn())
