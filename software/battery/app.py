import argparse
import socket
import sys
from lib import log
from lib import common

NAME = 'battery'

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

unix_socket_path = '/tmp/pisugar-server.sock'

client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

try:
    client_socket.connect(unix_socket_path)
    client_socket.send(b'get battery')
    received_data = client_socket.recv(128)
    log.debug(f'received {sys.getsizeof(received_data)} bytes')
    log.info(received_data.decode('utf-8'))

    client_socket.send(b'get temperature')
    received_data = client_socket.recv(128)
    log.debug(f'received {sys.getsizeof(received_data)} bytes')
    log.info(received_data.decode('utf-8'))
finally:
    client_socket.close()
