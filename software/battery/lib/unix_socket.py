import os
import stat
import socket
import sys
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


def send(_socket_client, _command, receive_buffer=256):
    try:
        _socket_client.send(_command.encode('utf-8'))

        received_data = ''
        while True:
            chunk = _socket_client.recv(receive_buffer).decode('utf-8')
            if not chunk:
                break  # no more data to receive
            received_data += chunk

        received_data = received_data.replace('\n', '')

        log.debug(f"received '{received_data}' from Unix socket")
        return received_data
    except socket.error as err:
        raise err


def close(_socket_client):
    if _socket_client:
        _socket_client.close()
        log.debug('closed Unix socket connection')
