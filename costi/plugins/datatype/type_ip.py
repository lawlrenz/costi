# -*- coding: utf-8 -*-
try:
    import re
except ImportError:
    raise ImportError('Missing dependencies, please check readme.')

NAME = "ip"

regex = re.compile(
    r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', re.IGNORECASE)


def validate(searchbar_input):
    isvalid = regex.search(searchbar_input)
    if isvalid is None:
        return None
    else:
        return isvalid.group()


def get_type_name():
    return NAME
