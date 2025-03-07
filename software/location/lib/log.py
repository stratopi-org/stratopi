import os
import logging
import sys

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=log_level,
                    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',
                    force=True)

stdout_logging = logging.Logger(name='stdout_logging',
                                level=log_level)
stdout_stream = logging.StreamHandler(stream=sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
                                             datefmt='%Y-%m-%dT%H:%M:%S'))
stdout_logging.addHandler(stdout_stream)


def debug(_txt):
    return stdout_logging.debug(_txt)


def info(_txt):
    return stdout_logging.info(_txt)


def warning(_txt):
    # to stderr
    return logging.warning(_txt)


def error(_txt, exit_code=None):
    # to stderr
    logging.error(_txt)

    if isinstance(exit_code, int) and exit_code > 0:
        sys.exit(exit_code)
