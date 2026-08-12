import argparse
import ast
import json
import os
import select
import signal
import sys

import psycopg2
from lib import common, log, slack

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

def on_notify(data):
    channel = (data.get('_meta') or {}).get('channel')
    log.debug(f"({channel}) {data}")

    slack_txt = None

    if channel == 'battery':
        slack_txt = data

    elif channel == 'location':
        vertical_speed_mpm = data['vertical_speed_mpm']

        if vertical_speed_mpm is None:
            vertical_speed = '-'
            vertical_speed_icon = ':grey_question:'
        else:
            vertical_speed_mpm = float(vertical_speed_mpm)

            if vertical_speed_mpm > 0:
                vertical_speed_icon = ':arrow_up_small:'
            elif vertical_speed_mpm < 0:
                vertical_speed_icon = ':arrow_down_small:'
            else:
                vertical_speed_icon = ':black_circle_for_record:'

            vertical_speed = (
                f"{vertical_speed_mpm:.1f} m/min | "
                f"{common.meters_to_feet(vertical_speed_mpm)} ft/min"
            )

        slack_txt = '\n'.join([
            ':round_pushpin: *Location Update*',
            f"*Date:* `{data['date']}`",
            f"*Time:* `{data['time']}`",
            f"*Latitude:* `{data['latitude']}`",
            f"*Longitude:* `{data['longitude']}`",
            (
            f"*Altitude:* `{data['altitude_m']} m | "
            f"{common.meters_to_feet(data['altitude_m'])} ft`"
            ),
            f"*Vertical speed:* `{vertical_speed}` {vertical_speed_icon}",
            (
                f"*Speed:* `{data['speed_kn']} kn | "
                f"{common.knots_to_mps(data['speed_kn'])} m/s | "
                f"{common.knots_to_mph(data['speed_kn'])} mph`"
            ),
            f"*Course:* `{data['course_d']}°`",
            f"*Direction:* `{data['direction']}`",
         ])

    elif channel == 'environmental':
        slack_txt = data

    if slack_txt:
        slack.send_message(slack_txt)

conn = psycopg2.connect(os.environ['POSTGRES_URL'])
conn.autocommit = True
masked_postgres_url = common.mask_postgres_url_password(
    os.environ['POSTGRES_URL']
)
log.debug(f'connected to PostgreSQL ({masked_postgres_url})')

with conn.cursor() as cur:
    cur.execute("LISTEN battery_insert")
    log.info('listening on PostgreSQL \'battery_insert\'...')

    cur.execute("LISTEN environmental_insert")
    log.info('listening on PostgreSQL \'environmental_insert\'...')

    cur.execute("LISTEN location_insert")
    log.info('listening on PostgreSQL \'location_insert\'...')

while True:
    select.select([conn], [], [])

    conn.poll()

    while conn.notifies:
        notify = conn.notifies.pop(0)
        data = json.loads(notify.payload)

        # break coordinates into separate latitude and longitude keys
        if notify.channel == 'location_insert':
            longitude, latitude = ast.literal_eval(
                data.pop('coordinates')
            )

            data['latitude'] = latitude
            data['longitude'] = longitude

        data['_meta'] = {
            'channel': notify.channel.removesuffix('_insert'),
        }

        on_notify(data)
