import sys


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


def decimal_degrees_to_dms(_latitude, _longitude):
    def decimal_to_dms(_deg):
        d = int(_deg)
        m, s = divmod((_deg - d) * 60, 1)
        m = int(m)
        s *= 60
        return d, m, s

    lat_deg, lat_min, lat_sec = decimal_to_dms(_latitude)
    long_deg, long_min, long_sec = decimal_to_dms(_longitude)

    return (lat_deg, lat_min, lat_sec), (long_deg, long_min, long_sec)


def meters_to_feet(_meters):
    return "{:.0f}".format(float(_meters) * 3.28084)


def knots_to_mps(_knots):
    return "{:.1f}".format(float(_knots) * 0.514444)


def knots_to_mph(_knots):
    return "{:.0f}".format(float(_knots) * 1.15078)
