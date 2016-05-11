# -*- coding: utf-8 -*-
try:
    import json
    import urllib
    import urllib2
    import httplib
    from datetime import datetime
    import time
    import calendar
except ImportError:
    raise ImportError('Missing dependencies, please check readme.')

# you need to create your own virustotal account to use their api, its free
APIKEY = ""

# different adresses for different requests
ADR_FILE = "https://www.virustotal.com/vtapi/v2/file/report"
ADR_URL = "https://www.virustotal.com/vtapi/v2/url/report"
ADR_IP = "https://www.virustotal.com/vtapi/v2/ip-address/report"


def get_infos(params, adr):
    data = urllib.urlencode(params)
    req = urllib2.Request(adr, data)
    try:
        response = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        print e
        return False
    except urllib2.URLError, e:
        print e
        return False
    except httplib.HTTPException, e:
        print e
        return False

    read_resp = response.read()
    if len(read_resp) > 0:
        return json.loads(read_resp)
    else:
        return False


def fetch(source, local_data=None, validator=None, lookedup_resource=None):
    if APIKEY == "":
        print("No API Key set for virustotalapi.")
        return False
    if lookedup_resource is None:
        print("No input to lookup for virustotalapi")
        return False

    ipres = ""
    datatype = "md5"  # None
    if validator is None:
        return False
    else:
        for validator_iter in validator:
            isvalid = validator_iter.validate(lookedup_resource)
            if isvalid:
                datatype = validator_iter.get_type_name()

                # because detected ip adresses are always also valid urls, we check for resolutions for the ip first
                if datatype == "ip":
                    adr = ADR_IP
                    params = {"ip": lookedup_resource,
                              "apikey": APIKEY}
                    try:
                        response = urllib.urlopen('%s?%s' % (adr, urllib.urlencode(params))).read()
                    except Exception:
                        response_dict = []
                        break

                    try:
                        response_dict = json.loads(response)
                    except ValueError:
                        response_dict = []
                        break
                    if response_dict:
                        if response_dict["response_code"] == 1:
                            for entries in response_dict["resolutions"]:
                                ipres += entries["hostname"] + ", "
                            ipres = ipres.strip()[0:len(ipres)-2]
    if datatype == "md5":
        adr = ADR_FILE
        params = {"resource": lookedup_resource,
                  "apikey": APIKEY}
    elif datatype == "url":
        adr = ADR_URL
        params = {"resource": lookedup_resource,
                  "apikey": APIKEY}
    else:
        return False

    loaded_json = get_infos(params, adr)
    item_infos = []

    if loaded_json:
        if loaded_json["response_code"] == 1:
            malicious = 0.0
            positives = float(loaded_json["positives"])
            if positives > 0:
                malicious = (float(loaded_json["total"]) / 100.0) * positives
            if loaded_json["scan_date"] != "":
                adding_date = calendar.timegm(datetime.strptime(loaded_json["scan_date"], "%Y-%m-%d %H:%M:%S").timetuple())
            else:
                adding_date = time.time()

            if "scans" in loaded_json:
                scan = loaded_json["scans"]

            if datatype == "md5":
                filename = ""
                md5 = ""
                sha1 = ""
                sha256 = ""
                link = ""
                ip = ""

                if loaded_json["md5"] != "":
                    md5 = loaded_json["md5"]
                if loaded_json["sha1"] != "":
                    sha1 = loaded_json["sha1"]
                if loaded_json["sha256"] != "":
                    sha256 = loaded_json["sha256"]

                item_infos.append({"date": adding_date,
                                   "filename": filename,
                                   "md5": md5,
                                   "sha1": sha1,
                                   "sha256": sha256,
                                   "link": link,
                                   "ip": ip,
                                   "malicious": malicious,
                                   "scans": scan})
            if datatype == "ip":
                item_infos.append({"date": adding_date,
                                   "ip": lookedup_resource,
                                   "malicious": malicious})
            if datatype == "url":
                if len(ipres) == 0 or malicious == 0:
                    ipres = ""

                item_infos.append({"date": adding_date,
                                   "status": "",
                                   "url": lookedup_resource,
                                   "resolutions": ipres,
                                   "malicious": malicious,
                                   "scans": scan})

    return json.dumps(item_infos, indent=2, sort_keys=True)
