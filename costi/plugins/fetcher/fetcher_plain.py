# -*- coding: utf-8 -*-
try:
    import urllib2
    import json
    import time
    import os
    import subprocess
except ImportError:
    raise ImportError('Missing dependencies, please check readme.')


def fetch(source, local_data=None, validator=None, lookedup_resource=None):
    # fetches textfiles (lists) for respective information (urls, ips, ..)
    # arguments: source (from sourcelist) - information with source of textfile
    if len(validator) == 1:
        validator = validator[0]
    else:
        return False
    curr_status = ""  # possible values: online, offline "unknown" (where  for unknown it is left empty)
    source_url = source[2]
    data_type = source[3]
    update_type = source[7]

    # print("Fetching Data from " + source_url + ". This may take some time!")

    # check if rsync needed to fetch file
    filename = None
    commands = source_url.split(" ")
    if len(commands) > 1:
        if commands[0] == "rsync" and len(commands) == 4:
            url = commands[2].split("/")
            filename = url[len(url)-1]
            # noinspection PyBroadException
            try:
                os.system(source_url)
                textfile = open(filename, "r")
            except Exception:
                print "A Problem with rsync occured."
                return False

        # elif add some more commands here maybe
        else:
            print("This command is not yet supported: " + commands[0])
            return False
    else:
        try:
            textfile = urllib2.urlopen(source_url)
        except urllib2.HTTPError, e:
            print e
            return False
        except urllib2.URLError, e:
            print e
            return False
        except httplib.HTTPException, e:
            print e
            return False

    item_infos = []

    unix_tstamp = time.time()
    for line in textfile:  # filter empty lines from text parts
        stripped = line.strip()
        if validator is not None and "#" not in stripped:
            validated_content = validator.validate(stripped)
        else:
            validated_content = None

        if validated_content is not None:
            data = {data_type: validated_content,
                    "tag": source[4],
                    "date": unix_tstamp,
                    "malicious": 100,
                    "status": curr_status}
            if update_type == "a":  # check because of speed enhancement!
                if not any(d[data_type] == data[data_type] for d in local_data):  # slow for many entries (>10k)..
                    item_infos.append(data)
            elif update_type == "w":
                item_infos.append(data)
            else:
                return False
        # else:
        #     print("No fitting data of type: " + data_type + ". Error occured with: " + stripped)

    # cleanup
    if filename is not None:
        os.remove(filename)

    return json.dumps(item_infos, indent=2, sort_keys=True)

