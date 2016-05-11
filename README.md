Costi
=============

Costi can be used to collect Open Source Threat Intelligence and to search for specific Information in this data.
It provides the possibility to add further sources and datatypes.
You can use this tool either as a Webservice or the API to use the features implemented.

Dependencies
------------
* web.py
* pygal
* numpy
* exrex
* feedparser
* lxml
* pycurl

Usage
-----
You can start Costi by running `$ costi` in the Commandline. Keep in mind, that you must run Costi in the same directory, where you can find your
static folder, which contains images and stylesheets for the webinterface.

Webservice
----------

Based on web.py. Run `costi` in the Terminal to start the Webserver. The default Port is 8080.

API
---

See `costi_api.py`.

Plugins
-------

This software is developed in that way, that you can add all new kind of fetcher, datatypes and sources.
Even if it's possible to customize everything for your need, it is essential, to retain a pattern within the JSON data.

Fetcher plugins have to return the found data in a specific way, where the "tag" key is always optional (enables specific search later on) and the "adding_dates"
are UnixTimestamps as Integers. Because of different kind of data, there is also the "malicious" key, which can be set to a float between 0-100.

Examples:

1. IP Adresses

```json
[
    {
        "adding_date": 1455612707.937708, 
        "ip": "1.189.118.162", 
        "malicious": 100.0,
        "status": "unknown", 
        "tag": "ftp"
    }, ...
]
```

2. MD5
```json
[
    {
        "adding_date": 1453330800.0, 
        "filename": "89hg56fd.exe", 
        "ip": "202.191.112.60",
        "link": "hxxp://202.191.112.60/~n02022-1/98jh6d5/89hg56fd.exe", 
        "malicious": 80.9,
        "malware_type": "Malware.Win32.Sample", 
        "md5": "34781D4F8654F9547CC205061221AEA5", 
        "sha1": "8E1D6C0032676A7EB2894FD3C5F4A9D0F5086459", 
        "sha256": "89C73C42E8CD8D20AAC5878C4585B9BE2CE12447D6B201D3BD1407142DD60BBF"
    }, ...
]
```

3. URLs (like IPs)
```json
[
    {
        "adding_date": 1455612734.785017, 
        "malicious": 5.0,
        "status": "unknown", 
        "tag": "", 
        "url": "000007.ru"
    }, ...
]
```


Fetcher and Cache
-----------------
As there are a lot of different sources, we need to fetch some sources in a different way than others. This tool
comes with a plain text fetcher (e.g. simple blocklists), a fetcher for rss feeds (eventually needs adjustments for other rss feeds,
because of deviations in the structure of the delivered data) and some fetchers for specific websites like vxvault and virustotal.

This tool delivers a caching module, to enable fast access to huge amounts of data. Sadly, there are sources which we cant cache completely, like virustotal. 
Hence we need to differ between them and query the local source as well as these kind of online sources when a request comes in. For the caching sources
it is also important to differ between sources where only new data is added and old data still remains (so we only need to append these new data), or if
the delivered data is completely or in parts exchanged (so we need to overwrite the whole local data).

Structure of sources.csv
------------------------
0. ID
1. source domain
2. url to data or the "bash way" to get data like `rsync -z psbl-mirror.surriel.com::psbl/psbl.txt`
3. datatype/s
4. tags (optional)
5. description (optional)
6. fetcher plugin
7. update_type (overwrite/Append only)
8. caching (true/false)

You can deactivate a source by commenting them out with a Hashtag (#).


Data Types
----------
Data types are modules in a specific plugin folder (plugins/datatype/). They are used to validate the search input as well
as helping the fetcher modules to find matching data. These modules have to contain the following functions to work fine:

* `def validate(someinput):`
Returns a valid output Group when someinput contains it and None if not. Regular expressions are great here.

* `def get_type_name():`
Returns the name of the validation type (ip, md5, ..).


Roadmap
-------
* Implement further sources/datatypes
* Use NGINX/Apache instead of web.py developement server
* Use a relational database instead of JSON files as cache
