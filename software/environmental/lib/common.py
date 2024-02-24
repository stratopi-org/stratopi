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


def cleanup_data(_input, str_format="{:.1f}"):
    split_pieces = _input.split(': ')
    if len(split_pieces) == 2:
        try:
            numeric_value = float(split_pieces[1])
            if numeric_value.is_integer():  # check if is an integer
                return "{:.0f}".format(numeric_value)  # format as flat integer

            return str_format.format(numeric_value)  # format with str_format
        except ValueError:
            log.warning("value error in 'common.cleanup_data()'")
            return _input  # return original if conversion to numeric fails
    else:
        log.warning("splitting on ': ' did not return exactly 2 pieces")
        return _input  # return original if splitting fails
