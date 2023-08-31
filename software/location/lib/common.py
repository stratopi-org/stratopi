import sys
from lib import log


def strip_list_elements(_list):
    stripped_list = [element.strip() for element in _list]
    return stripped_list


def mps_to_knots(_mps):
    return _mps * 1.94384449


def mps_to_mph(_mps):
    return _mps * 2.23693629


def meters_to_feet(_meters):
    return _meters * 3.28084
