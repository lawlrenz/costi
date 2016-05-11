# -*- coding: utf-8 -*-
try:
    import csv
    import plugins.plugin_handler as ph
    import os
    import inspect
except ImportError:
    raise ImportError('Missing dependencies, please check readme.')

SOURCE_FLE_NAME = "sources/sources.csv"
DELIMITER = ";"
CACHE_DIR = 'cache/'

path_of_executing_sourcepool_py = inspect.stack()[0][1].split('/')
path_of_executing_package = path_of_executing_sourcepool_py[0:len(path_of_executing_sourcepool_py) - 1]
CACHE_DIR = '/'.join(path_of_executing_package) + '/' + CACHE_DIR
SOURCE_FLE_NAME = '/'.join(path_of_executing_package) + '/' + SOURCE_FLE_NAME


def _get_all_sources_as_list():
    """ open source file and save data in array """
    all_sources = []
    with open(SOURCE_FLE_NAME, "r") as csvfile:
        source_reader = csv.reader(csvfile, delimiter=DELIMITER)
        for row in source_reader:
            if "#" not in row[0]:
                all_sources.append(row)

    return all_sources


def get_sources(datatypes=None, tags=None, ident=None, name=None):
    """
    Returns sources which maches all criterion (datatypes, tags, ident, name)
    :param datatypes:
    :param tags:
    :param ident:
    :param name:
    :return:
    """
    if tags is None:
        tags = []
    if datatypes is None:
        datatypes = []
    if type(datatypes) != list:
        datatypes = [datatypes]

    all_sources = _get_all_sources_as_list()
    # eliminate sources that do not fit looked up type
    looked_up_sources = []
    for source in range(len(all_sources)):
        source_types = all_sources[source][3].split(',')

        if (all_sources[source][0] == ident or ident is None) \
                and (all_sources[source][1] == name or name is None) \
                and (bool(set(source_types) & set(datatypes)) or len(datatypes) == 0) \
                and (all_sources[source][4] in tags or len(tags) == 0):
            looked_up_sources.append(all_sources[source])

    if len(looked_up_sources) == 0:
        print("Source does not exist with following criterion:\n"
              "# datatypes: [" + ','.join(datatypes) + "]\n"
              "# tags: [" + ','.join(tags) + "]\n"
              "# ID: " + str(ident) + "\n"
              "# name: " + str(name))
    return looked_up_sources


def add_source(provider, link, data_type, fetcher, caching, tag="",
               description="", update_type="a", trans_rating="None"):
    """
    Adds new source to source file. Can also be done manually.
    :param provider: not optional
    :param link: not optional
    :param data_type: not optional
    :param fetcher: not optional
    :param caching: optional
    :param tag: optional
    :param description: optional
    :param update_type: optional - can be set to "a" for append or "w" for overwrite
    :param trans_rating: optional - default set to None, can be between 0 and 1 with dots (e.g. 0.3)
    :return: True (everything fine) or False (source exist or fetcher does not)
    """
    existing_sources = _get_all_sources_as_list()

    existing_ids = []
    for source in range(len(existing_sources)):  # check if source already exists
        if link in existing_sources[source][2] and data_type in existing_sources[source][2]:
            return False
        existing_ids.append(existing_sources[source][0])

    ident = 0
    while ident in existing_ids:
        ident += 1

    if trans_rating is not None:
        if not 0.0 <= trans_rating <= 1.0:
            return False

    existing_sources.append([ident, provider, link, data_type.lower(), tag.lower(),
                             description, fetcher.lower(), update_type.lower(), caching, trans_rating])

    fittingplugins = ph.get_plugins("fetcher", fetcher)  # check if plugin for fetching data exists
    if len(fittingplugins) == 0:
        return False

    with open(SOURCE_FLE_NAME, 'w+') as csvfile:
        sourcewriter = csv.writer(csvfile, delimiter=DELIMITER, quoting=csv.QUOTE_ALL)
        for i in range(len(existing_sources)):
            sourcewriter.writerow(existing_sources[i])

    return True


def rm_source(identnr):
    """removes source with input identnr
    :param identnr:
    """
    source = get_sources(ident=str(identnr))
    if source:
        source_name = source[0][1]
    else:
        return False

    path = CACHE_DIR + str(identnr) + "_" + source_name.replace(".", "") + '.json'

    all_sources = _get_all_sources_as_list()
    new = [x for x in all_sources if x[0] != identnr]

    with open(SOURCE_FLE_NAME, 'w+') as csvfile:
        sourcewriter = csv.writer(csvfile, delimiter=DELIMITER, quoting=csv.QUOTE_ALL)
        for row in new:
            sourcewriter.writerow(row)

    if os.remove(path):
        return True
    else:
        return False