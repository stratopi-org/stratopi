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


def cleanup_data(_input):
    split_pieces = _input.split(': ')
    if len(split_pieces) >= 2:
        try:
            # return in the same format as PostgreSQL will concert to NUMERIC(4, 1)
            numeric_value = float(split_pieces[1])
            formatted_value = "{:.1f}".format(numeric_value)
            return formatted_value
        except ValueError:
            return _input
    else:
        return _input
