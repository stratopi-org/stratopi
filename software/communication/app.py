import argparse
import os
import select
import signal
import sys

import psycopg2
from lib import common, log

NAME = 'communication'

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

conn = None

def handle_shutdown(signum, frame):
    if conn:
        conn.close()
        log.debug('closed PostgreSQL connection')

    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

def process_battery(data):
    log.debug(f'channel=battery_insert | {data}')

def process_environmental(data):
    log.debug(f'channel=environmental_insert | {data}')

def process_location(data):
    log.debug(f'channel=location_insert | {data}')

conn = psycopg2.connect(os.environ['POSTGRES_URL'])
conn.autocommit = True
masked_postgres_url = common.mask_postgres_url_password(
    os.environ['POSTGRES_URL']
)
log.debug(f'connected to PostgreSQL ({masked_postgres_url})')

with conn.cursor() as cur:
    cur.execute("LISTEN battery_insert")
    log.info('listening for PostgreSQL battery notify events...')

    cur.execute("LISTEN environmental_insert")
    log.info('listening for PostgreSQL environmental notify events...')

    cur.execute("LISTEN location_insert")
    log.info('listening for PostgreSQL location notify events...')

while True:
    select.select([conn], [], [])

    conn.poll()

    while conn.notifies:
        notify = conn.notifies.pop(0)

        if notify.channel == 'battery_insert':
            process_battery(notify.payload)

        elif notify.channel == 'environmental_insert':
            process_environmental(notify.payload)

        elif notify.channel == 'location_insert':
            process_location(notify.payload)
