# -*- coding: utf-8 -*-
try:
    import lxml.html as html
    import requests
    import json
    from datetime import date
    import time
except ImportError:
    raise ImportError('Missing dependencies, please check readme.')

# config
START = 0
STEP_RANGE = 40
AMOUNT_LIMIT = None


def get_detail_information(id_link):
    try:
        item_page = requests.get('http://vxvault.net/' + id_link)
    except requests.ConnectionError, e:
        print e
        return False
    tree_item_page = html.fromstring(item_page.content)

    detail_info_tags = tree_item_page.xpath('//div[@id="page"]/b/text()')

    detail_info_text_filtered = []
    detail_info_text = tree_item_page.xpath('//div[@id="page"]/text()')

    for line in detail_info_text:  # filter empty lines from text parts
        stripped = line.strip()
        if stripped != "":
            detail_info_text_filtered.append(stripped)

    malware_type = tree_item_page.xpath('//div[@id="page"]/h3/text()')[0].strip()
    adding_date = ""
    filename = ""
    md5 = ""
    sha1 = ""
    sha256 = ""
    link = ""
    ip = ""
    for itr in range(len(detail_info_tags)):
        if detail_info_tags[itr] == "Added:":
            datetime = detail_info_text_filtered[itr].split('-')
            if len(datetime) == 3:
                y = int(datetime[0])
                m = int(datetime[1])
                d = int(datetime[2])
                if y != 0 and m != 0 and d != 0:
                    start = date(y, m, d)
                    adding_date = time.mktime(start.timetuple())
                else:
                    adding_date = time.time()

            else:
                adding_date = time.time()
        elif detail_info_tags[itr] == "File:":
            filename = detail_info_text_filtered[itr]
        elif detail_info_tags[itr] == "MD5:":
            md5 = detail_info_text_filtered[itr]
        elif detail_info_tags[itr] == "SHA-1:":
            sha1 = detail_info_text_filtered[itr]
        elif detail_info_tags[itr] == "SHA-256:":
            sha256 = detail_info_text_filtered[itr]
        elif detail_info_tags[itr] == "Link:":
            link = detail_info_text_filtered[itr]
        elif detail_info_tags[itr] == "IP:":
            ip = detail_info_text_filtered[itr]

    return {"date": adding_date,
            "malware_type": malware_type,
            "filename": filename,
            "md5": md5,
            "sha1": sha1,
            "sha256": sha256,
            "link": link,
            "ip": ip,
            "malicious": 100}


def fetch(source, local_data=None, validator=None, lookedup_resource=None):
    source_url = source[2]
    # print("Fetching Data from " + source_url + ". This may take some time (hours)!")
    item_infos = []
    step = START
    endofnewdata = False
    while (step <= AMOUNT_LIMIT or AMOUNT_LIMIT is None) and not endofnewdata:
        # slow! atm ~2h for whole download. multithreaded?
        generated_link = source_url + '?s=' + str(step) + '&m=' + str(STEP_RANGE)
        try:
            page = requests.get(generated_link)
        except requests.ConnectionError, e:
            print e
            return False
        tree_page = html.fromstring(page.content)
        id_links = tree_page.xpath('//div[@id="page"]/table/tr/td[1]//@href')
        if len(id_links) == 0:
            break
        else:
            for id_link in id_links:
                # print id_link
                detail = get_detail_information(id_link)
                if detail:
                    if not any(d['md5'] == detail['md5'] for d in local_data):
                        item_infos.append(detail)
                    else:
                        endofnewdata = True
                        break
                else:
                    return False
        step += STEP_RANGE

    return json.dumps(item_infos, indent=2)  # , sort_keys=True)
