import math
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


def decimal_degrees_to_dms(latitude, longitude, as_string=False):
    latitude = float(latitude)
    longitude = float(longitude)

    if not math.isfinite(latitude) or not math.isfinite(longitude):
        raise ValueError("coordinates must be finite numbers")

    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90 degrees")

    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180 degrees")

    def decimal_to_dms(value):
        negative = value < 0

        # Rounding total seconds first handles carry into minutes/degrees.
        total_seconds = round(abs(value) * 3600, 3)

        degrees = int(total_seconds // 3600)
        remainder = total_seconds % 3600
        minutes = int(remainder // 60)
        seconds = remainder % 60

        return degrees, minutes, seconds, negative

    lat_deg, lat_min, lat_sec, lat_negative = decimal_to_dms(latitude)
    lon_deg, lon_min, lon_sec, lon_negative = decimal_to_dms(longitude)

    if as_string:
        lat = (
            f"{lat_deg}° {lat_min}′ {lat_sec:.3f}″ "
            f"{'S' if lat_negative else 'N'}"
        )
        lon = (
            f"{lon_deg}° {lon_min}′ {lon_sec:.3f}″ "
            f"{'W' if lon_negative else 'E'}"
        )
        return lat, lon

    # Including direction avoids the ambiguous “negative zero degrees” problem.
    return (
        (lat_deg, lat_min, lat_sec, "S" if lat_negative else "N"),
        (lon_deg, lon_min, lon_sec, "W" if lon_negative else "E"),
    )


def meters_to_feet(_meters):
    return f"{float(_meters) * 3.28084:.1f}"


def knots_to_mps(_knots):
    return f"{float(_knots) * 0.514444:.1f}"


def knots_to_mph(_knots):
    return f"{float(_knots) * 1.15078:.0f}"
