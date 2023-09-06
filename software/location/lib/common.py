import sys
from lib import log


def python_version():
    if not sys.version_info:
        return 'Python'

    return f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'


def sec_to_min(_input):
    return int(_input / 60)


def mask_postgres_url_password(_input):
    scheme = _input.split('//')[0]
    url_parts = _input.split('//')[1].split('@')
    username_password = url_parts[0].split(':')
    username = username_password[0]
    masked_password = '*' * len(username_password[1])
    return f"{scheme}//{username}:{masked_password}@{url_parts[1]}"


def strip_list_elements(_list):
    stripped_list = [element.strip() for element in _list]
    return stripped_list


def mps_to_knots(_mps):
    return _mps * 1.94384449


def mps_to_mph(_mps):
    return _mps * 2.23693629


def meters_to_feet(_meters):
    return _meters * 3.28084
