import sys
import math
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


def format_data(_input, str_format="{:.1f}"):
    try:
        numeric_value = float(_input)
        if numeric_value.is_integer():  # check if is an integer
            return "{:.0f}".format(numeric_value)  # format as flat integer

        return str_format.format(numeric_value)  # format with str_format
    except ValueError:
        log.warning("value error in 'common.cleanup_data()'")
        return _input  # return original if conversion to numeric fails


def celsius_to_fahrenheit(_celsius):
    return (_celsius * 9/5) + 32


def hectopascal_to_bar(_hectopascal):
    return _hectopascal / 1000


def hectopascal_to_psi(_hectopascal):
    return _hectopascal * 0.0145038
