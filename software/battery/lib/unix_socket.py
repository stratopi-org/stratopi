import socket
import os
import stat
import sys
from lib import log

client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)


def is_socket(_input):
    try:
        file_stat = os.stat(_input)
        return stat.S_ISSOCK(file_stat.st_mode)
    except OSError as err:
        raise err


def connect(_unix_socket_path):
    if not is_socket(_unix_socket_path):
        raise IOError(f"path '{_unix_socket_path}' is not a unix socket")
    client_socket.connect(_unix_socket_path)


def send(_command, receive_buffer=256):
    try:
        client_socket.send(_command.encode('utf-8'))
        received_data = client_socket.recv(receive_buffer)
        received_bytes = sys.getsizeof(received_data)
        log.debug(f'received {received_bytes} bytes via unix socket')

        if received_bytes >= receive_buffer:
            log.warning(
                f"received {received_bytes} bytes which is the limit of the "
                f"unix socket buffer. consider increasing 'receive_buffer' from "
                f"{receive_buffer} bytes"
            )

        return received_data.decode('utf-8').strip()
    except socket.error as err:
        raise err


def close():
    client_socket.close()
    log.debug('closed unix socket connection')
