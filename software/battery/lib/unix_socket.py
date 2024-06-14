import os
import stat
import socket
import time
from lib import log


def is_socket(_input):
    try:
        file_stat = os.stat(_input)
        return stat.S_ISSOCK(file_stat.st_mode)
    except OSError as err:
        raise err


def connect(_unix_socket_path):
    if not is_socket(_unix_socket_path):
        raise IOError(f"'{_unix_socket_path}' is not a Unix socket")
    socket_client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    socket_client.connect(_unix_socket_path)
    log.debug(f"connected to Unix socket '{_unix_socket_path}'")
    return socket_client


def send(_socket_client, _command, receive_buffer=1024):
    try:
        _socket_client.send(_command.encode('utf-8'))
        raw_received_data = _socket_client.recv(receive_buffer).decode('utf-8').strip().replace('\n', '')
        log.debug(f"received '{raw_received_data}' from Unix socket")

        received_data = raw_received_data.replace('single', '')

        if not received_data:
            log.warning('received data from Unix socket which is ignored. Retrying send...')
            time.sleep(0.05)
            return send(_socket_client, _command, receive_buffer)

        return received_data
    except (socket.error, UnicodeDecodeError) as err:
        raise err


def close(_socket_client):
    if _socket_client:
        try:
            socket_client_path = _socket_client.getpeername()
            _socket_client.close()
            log.debug(f"closed Unix socket connection to '{socket_client_path}'")
        except socket.error:
            pass
