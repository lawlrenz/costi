# -*- coding: utf-8 -*-

try:
    import feedparser
    import json
    import time
    from datetime import date
except ImportError:
    raise ImportError('Missing dependencies, please check readme.')


def make_timestamp(date_str):
    datetime = date_str.split('/')
    if len(datetime) == 1:
        datetime = date_str.split('-')
    if len(datetime) == 1:
        datetime = date_str.split('.')

    m = None
    y = None
    d = None
    if len(datetime) == 3:
        for i in range(len(datetime)):
            if len(datetime[i]) == 4 and (1900 <= int(datetime[i]) <= 2200):
                y = int(datetime[i])
            elif len(datetime[i]) == 3:
                m = datetime[i]
                if m == "Jan":
                    m = 1
                elif m == "Feb":
                    m = 2
                elif m == "Mar":
                    m = 3
                elif m == "Apr":
                    m = 4
                elif m == "May":
                    m = 5
                elif m == "Jun":
                    m = 6
                elif m == "Jul":
                    m = 7
                elif m == "Aug":
                    m = 8
                elif m == "Sep":
                    m = 9
                elif m == "Oct":
                    m = 10
                elif m == "Nov":
                    m = 11
                elif m == "Dec":
                    m = 12
            elif 1 <= len(datetime[i]) <= 2:
                if d is None:
                    d = int(datetime[i])
                else:
                    m = int(datetime[i])
        start = date(y, m, d)
        adding_date = time.mktime(start.timetuple())

    else:
        adding_date = time.time()

    return adding_date


def fetch(source, local_data=None, validator=None, lookedup_resource=None):
    if len(validator) == 1:
        validator = validator[0]
    else:
        return False
    curr_status = ""  # can also be online or offline
    source_url = source[2]
    data_type = source[3]
    update_type = source[7]

    feed = feedparser.parse(source_url)
    item_infos = []

    rss_items = feed['items']

    for key in rss_items:
        title = key["title_detail"]["value"]
        if len(source[4]) == 0:
            tag = title
        else:
            tag = source[4]

        information = key["link"]
        date_str = key["description"]
        adding_date = make_timestamp(date_str)

        if validator is not None:
            validated_content = validator.validate(information)
        else:
            validated_content = None

        if validated_content is not None:
            data = {data_type: validated_content,
                    "tag": tag,
                    "date": adding_date,
                    "malicious": 100,
                    "status": curr_status}

        if update_type == "a":  # check because of speed enhancement!
            if not any(d[data_type] == data[data_type] for d in local_data):  # slow for many entries (>10k)..
                item_infos.append(data)
        elif update_type == "w":
            item_infos.append(data)
        else:
            return False

    return json.dumps(item_infos, indent=2, sort_keys=True)
