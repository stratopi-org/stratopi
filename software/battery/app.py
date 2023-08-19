import argparse
import asyncio
from lib import log
from lib import common
from lib import unix_socket

NAME = 'battery'
UNIX_SOCKET_PATH = '/tmp/pisugar-server.sock'
SLEEP_TIME = 60

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
log.info(f'refreshing prices every {common.sec_to_min(SLEEP_TIME)} minute(s)')
asyncio.run(loop_fn())


async def loop_fn():
    while True:
        try:
            unix_socket.connect(UNIX_SOCKET_PATH)
            log.info(unix_socket.send(f'get battery'))
        except Exception as err:
            log.error(err)
        finally:
            unix_socket.close()

        await asyncio.sleep(SLEEP_TIME)
