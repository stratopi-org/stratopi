import sys
from lib import log


def strip_list_elements(_list):
    stripped_list = [element.strip() for element in _list]
    return stripped_list
