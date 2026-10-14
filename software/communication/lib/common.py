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


def format_measurement(value, unit, converter=None):
    if value is None:
        return 'null'

    if converter is not None:
        value = converter(value)

    return f'{value}{unit}'


def celsius_to_fahrenheit(_celsius):
    return f"{(_celsius * 9 / 5) + 32:.1f}"


def hectopascal_to_bar(_hectopascal):
    return f"{float(_hectopascal) / 1000:.3f}"


def hectopascal_to_inhg(_hectopascal):
    return f"{_hectopascal * 0.029529983:.2f}"


def hectopascal_to_psi(_hectopascal):
    return f"{float(_hectopascal) * 0.0145038:.2f}"


def pressure_to_altitude(_hectopascal):
    return f"{44330.77 * (1 - (_hectopascal / 1013.25) ** 0.190263):.1f}"


def meters_to_feet(_meters):
    return f"{float(_meters) * 3.28084:.0f}"


def knots_to_mps(_knots):
    return f"{float(_knots) * 0.514444:.1f}"


def knots_to_mph(_knots):
    return f"{float(_knots) * 1.15078:.0f}"

