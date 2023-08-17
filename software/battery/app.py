import socket
import sys

unix_socket_path = '/tmp/pisugar-server.sock'

client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

try:
    client_socket.connect(unix_socket_path)
    client_socket.send(b'get battery')
    received_data = client_socket.recv(256)
    print(f'received bytes: {sys.getsizeof(received_data)}')
    print(received_data.decode('utf-8'))
finally:
    client_socket.close()
