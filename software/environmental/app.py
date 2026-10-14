import argparse
import asyncio
import os
import time

import bme280
import board
import psycopg2
import smbus2
from adafruit_ms8607 import MS8607
from lib import common, log, pi

NAME = 'environmental'
SLEEP_TIME = 60 * 1   # 1 minute
BME280_ADDRESS = 0x77

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

ms8607 = None
calibration_params = None

max_attempts = 3

# initialize BME280 (internal)
for attempt in range(1, max_attempts + 1):
    try:
        calibration_params = bme280.load_calibration_params(
            bus,
            BME280_ADDRESS,
        )
        break
    except OSError as err:
        log.warning(
            f'failed to initialize Bosch BME280 '
            f'(attempt {attempt}/{max_attempts}): {err}'
        )

        if attempt < max_attempts:
            time.sleep(2)

# initialize MS8607 (external)
for attempt in range(1, max_attempts + 1):
    try:
        ms8607 = MS8607(board.I2C())

        # verify sensor communication
        _ = ms8607.temperature
        _ = ms8607.pressure
        _ = ms8607.relative_humidity

        break
    except (OSError, RuntimeError, ValueError) as err:
        log.warning(
            f'failed to initialize Adafruit MS8607 '
            f'(attempt {attempt}/{max_attempts}): {err}; retrying...'
        )

        if attempt < max_attempts:
            time.sleep(2)

async def loop_fn():
    while True:
        in_temperature = None
        in_pressure = None
        in_humidity = None

        ex_temperature = None
        ex_pressure = None
        ex_humidity = None

        # BME280 (internal)
        if calibration_params is not None:
            try:
                data = bme280.sample(bus, BME280_ADDRESS, calibration_params)

                in_temperature = common.format_data(data.temperature)
                in_pressure = common.format_data(data.pressure)
                in_humidity = common.format_data(data.humidity)

            except (OSError, RuntimeError, ValueError) as err:
                in_temperature = None
                in_pressure = None
                in_humidity = None
                log.warning(f'failed to read Bosch BME280: {err}')

        # MS8607 (external)
        if ms8607 is not None:
            try:
                ex_temperature = common.format_data(ms8607.temperature)
                ex_pressure = common.format_data(ms8607.pressure)
                ex_humidity = common.format_data(ms8607.relative_humidity)

            except (OSError, RuntimeError, ValueError) as err:
                ex_temperature = None
                ex_pressure = None
                ex_humidity = None
                log.warning(f'failed to read Adafruit MS8607: {err}')

        conn = psycopg2.connect(os.environ['POSTGRES_URL'])
        masked_postgres_url = common.mask_postgres_url_password(
            os.environ['POSTGRES_URL'])
        log.debug(f'connected to PostgreSQL ({masked_postgres_url})')

        cursor = conn.cursor()

        try:
            cpu_temperature = pi.get_cpu_temperature()

            cursor.execute(
                'INSERT INTO environmental (in_temperature_c, in_pressure_hpa, in_humidity_rh, ex_temperature_c, ex_pressure_hpa, ex_humidity_rh, cpu_temperature_c) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (in_temperature, in_pressure, in_humidity,
                 ex_temperature, ex_pressure, ex_humidity,
                 cpu_temperature)
            )

            conn.commit()

            log.info(
                f'inserted {NAME} data internal_temp={in_temperature}°C, internal_pressure={in_pressure} hPa, internal_humidity={in_humidity}% RH, external_temp={ex_temperature}°C, external_pressure={ex_pressure} hPa, external_humidity={ex_humidity}% RH, cpu_temp={cpu_temperature}°C into PostgreSQL'
            )

        except Exception as err:
            conn.rollback()
            log.error(err)
        finally:
            cursor.close()
            conn.close()
            log.debug('closed PostgreSQL connection')

        await asyncio.sleep(SLEEP_TIME)

asyncio.run(loop_fn())
