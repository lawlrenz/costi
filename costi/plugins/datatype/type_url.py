# -*- coding: utf-8 -*-
try:
    import re
except ImportError:
    raise ImportError('Missing dependencies, please check readme.')

NAME = "url"

# thanks to "cetver" from github
regex = re.compile(
    r'(?:(?:http|ftp)s?://)?'  # http:// or https://, ftp:// or ftps://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)', re.IGNORECASE)


def validate(searchbar_input):
    isvalid = regex.search(searchbar_input)
    if isvalid is None:
        return None
    else:
        return isvalid.group()


def get_type_name():
    return NAME
