import sys


def python_version():
    if not sys.version_info:
        return 'Python'

    return f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'


def mask_postgres_url_password(_input):
    scheme = _input.split('//')[0]
    url_parts = _input.split('//')[1].split('@')
    username_password = url_parts[0].split(':')
    username = username_password[0]
    masked_password = '*' * len(username_password[1])
    return f"{scheme}//{username}:{masked_password}@{url_parts[1]}"
