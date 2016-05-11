# -*- coding: utf-8 -*-

try:
    import json
    import plugins.plugin_handler as ph
    import costi_sourcepool as sp
    import sys
    import os.path
    import threading
    import numpy
    import time
    import exrex
    import random
    import pycurl
    from io import BytesIO
    import os
    import inspect
except ImportError:
    raise ImportError('Missing dependencies, please check readme.')

# config
CACHE_DIR = 'cache/'
path_of_executing_cache_py = inspect.stack()[0][1].split('/')
path_of_executing_package = path_of_executing_cache_py[0:len(path_of_executing_cache_py) - 1]
CACHE_DIR = '/'.join(path_of_executing_package) + '/' + CACHE_DIR


def _open_file(fullfilename, mode='r+'):
    """
    :param fullfilename:
    :param mode:
    :return: filehandle
    """
    try:
        res = open(fullfilename, mode)
    except IOError:
        sys.exit('IOError while accessing file ' + fullfilename + '.')
    else:
        return res


def get_local_storage_info(identnr):
    """
    if there does not exist local data, it is created in the CACHE_DIR which is also be created if it does not exist
    :param identnr:
    :return: loaded list with dictionaries and the path to the file
    """

    source = sp.get_sources(ident=str(identnr))
    if source:
        source_name = source[0][1]
    else:
        return False

    cache_dir = os.path.dirname(CACHE_DIR)
    path = CACHE_DIR + str(identnr) + "_" + source_name.replace(".", "") + '.json'

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    if not os.path.isfile(path):
        new_file = _open_file(path, 'w')
        json.dump([], new_file)
        new_file.close()

    filehandle = _open_file(path, 'r')
    loaded_old = json.load(filehandle)
    filehandle.close()

    return loaded_old, path


def merge_data_with_local_storage(identnr, json_data):
    """
    merges the input json_data with the local data for input id
    there will not be any duplicates as such,
    but two similar (e.g. one is missing md5, the other sha1) entries wont be merged!
    :param identnr:
    :param json_data:
    :return: False if something went wring
    """

    loaded_old, path = get_local_storage_info(identnr)
    loaded_new = json.loads(json_data)

    source = sp.get_sources(ident=identnr)  # get update_type for source
    if source and len(source) == 1:
        update_type = source[0][7]
    else:
        print("Error while loading source information with ID " + identnr)
        return False

    if update_type == "a":
        updated = loaded_old + [x for x in loaded_new if x not in loaded_old]
    elif update_type == "w":
        updated = loaded_new
    else:
        print("This update_type is not yet implemented: " + update_type)
        return False

    filehandle_write = _open_file(path, 'w')
    json.dump(updated, filehandle_write, indent=2, sort_keys=True)
    filehandle_write.close()


def fetch_data(identnr, lookedup_resource=None):
    """
    fetches data from a source
    improvements - maybe small bunches of data not all at once for better performance
    :param lookedup_resource:
    :param identnr:
    :return: json_data fetched from source
    """
    local_data, _ = get_local_storage_info(identnr)
    source = sp.get_sources(ident=str(identnr))
    if source:
        fetcher_plugin = source[0][6]
        datatypes = source[0][3].split(",")

        # loading fetcher for source
        plugin = ph.get_plugins("fetcher", pluginname=fetcher_plugin)
        if plugin and len(plugin) == 1:
            fetcher = ph.load_plugin(plugin[0])
        else:
            print("Error while loading Plugin.")
            return False

        # loading validators for datatypes with pluginhandler
        validators = []
        for datatype_iter in datatypes:
            datatype_iter = datatype_iter.strip()
            plugin_validate = ph.get_plugins("datatype", pluginname=datatype_iter)

            if plugin_validate and len(plugin_validate) == 1:
                validators.append(ph.load_plugin(plugin_validate[0]))
            else:
                print("Error while loading Validationplugin " + datatype_iter + " for source ID " + str(identnr))
                return False

        # finally fetch data from source
        json_data = fetcher.fetch(source[0],
                                  local_data=local_data,
                                  validator=validators,
                                  lookedup_resource=lookedup_resource)
        return json_data
    else:
        return False


def update_local_storage(identnr=None, verbose=False):
    """
    merges automatically new data into old
    :param verbose: for additional text output on console
    :param identnr:
    :return: new fetched data as json list or false if nothing new
    """

    return_list = []
    all_idents = []
    if identnr is None:
        sources = sp.get_sources()
        for source in sources:
            if source[8] == "True":
                all_idents.append(str(source[0]))
        if verbose:
            print("Updating Cache of all available sources. This may take some time.")
    else:
        sources = sp.get_sources(ident=str(identnr))
        if sources and sources[0][8] == "True":
            all_idents = [sources[0][0]]
            if verbose:
                print("Updating Cache of " + sources[0][1] + " with ID " + sources[0][0] + ". This may take some time.")
        else:
            return False
    for ident_iter in all_idents:
        if verbose:
            print("Fetching Data from Source " + str(ident_iter) + ". This may take some time!")
        fetched = fetch_data(ident_iter)
        if verbose:
            print("Done.")
        if fetched > 0 and fetched is not False:
            merge_data_with_local_storage(ident_iter, fetched)
            loaded = json.loads(fetched)
            if len(loaded) == 0:
                loaded = False
            return_list.append({"source_id": ident_iter, "new_data": loaded})
    print("Cache updated.")

    return json.dumps(return_list, indent=2, sort_keys=True)


def query_source_cache(ident, lookedup_resource):
    """
    Querys local cache for information about the looked_up resource in source with ID == ident
    :param ident:
    :param lookedup_resource:
    :return: information
    """

    stored_data, _ = get_local_storage_info(ident)
    infos = []
    for item_dict in stored_data:
        for key in item_dict:
            content = item_dict[key]
            resource_encoded = str(lookedup_resource).encode('utf-8').lower()
            if type(content) == unicode:
                content = content.encode('utf-8').lower()

            if content == resource_encoded:
                infos.append(item_dict)
    if len(infos) == 0:
        return False
    else:
        return infos


def query_source_direct(ident, lookedup_resource):
    """
    Fetching data from source directly
    :param ident:
    :param lookedup_resource:
    :return: json data found
    """
    fetched = fetch_data(ident, lookedup_resource=lookedup_resource)
    if fetched:
        return json.loads(fetched)
    else:
        return []


def query(lookedup_resource, datatypes=None, tags=None):
    """
    querys cache AND sources without cached data like virustotal
    also analyzes queried data (false/positives, amount etc)
    :param tags:
    :param datatypes:
    :param lookedup_resource:
    :return: collected json data and amount of queried sources
    """

    if datatypes is None:
        datatypes = []
    if tags is None:
        tags = []

    sources = sp.get_sources(tags=tags, datatypes=datatypes)

    query_data = []
    amount_sources = 0
    amount_negatives = 0.0
    amount_positives = 0.0
    amount_notlisted = 0.0
    amount_unclear = 0.0

    # query data
    for source in sources:
        amount_sources += 1
        cfr = float("{0:.2f}".format(get_confidence_rating(source[0])))
        result_id = "#{}:Confidence Rating: {} - {} <br/> {}".format(source[0], cfr, source[1], source[5])
        if source[8] == "True":  # query local cache
            local = query_source_cache(source[0], lookedup_resource)
            if local:
                query_data.append({result_id: local})
            else:
                amount_notlisted += 1

        elif source[8] == "False":  # query source directly
            online = query_source_direct(source[0], lookedup_resource)
            if len(online) == 0 or online is False:
                amount_notlisted += 1
            else:
                query_data.append({result_id: online})

    final_output = []
    cat_helper = {"other": 0.0}

    # add stats (false/positives, amount of sources, factorized tags with confidence rating) to final output
    for source in query_data:
        for hostname in source:
            source_id = hostname.split(":")[0]
            source_id = source_id[1:len(source_id)]
            conf_rat = float("{0:.2f}".format(get_confidence_rating(source_id)))

            for entry in source[hostname]:
                score = conf_rat * (float(entry["malicious"]) / 100.0)
                tags = []
                for key in entry:
                    if key == 'tag':
                        tags = entry["tag"].split(",")
                        break

                if len(tags) > 0:
                    for tag in tags:
                        does_key_exist = False
                        for key in cat_helper:
                            if key == tag:
                                does_key_exist = True
                                break
                        if does_key_exist:
                            cat_helper[tag] += score
                        else:
                            cat_helper[tag] = score
                else:
                    cat_helper["other"] += score

                if float(entry["malicious"]) == 100:
                    amount_positives += 1
                    break
                elif float(entry["malicious"]) == 0:
                    amount_negatives += 1
                else:
                    amount_unclear += 1
    for entry in cat_helper:
        cat_helper[entry] = "{0:.2f}".format(float(cat_helper[entry]))

    stats_dic = [{"Queried Sources": amount_sources,
                  "Negatives": amount_negatives,
                  "Positives": amount_positives,
                  "Not contained in": amount_notlisted,
                  "Unclear": amount_unclear}, {"ressource": lookedup_resource}, cat_helper]

    final_output.append(stats_dic)

    # add the results from query to final output
    final_output.append(query_data)

    # you can add more stuff here ..
    return json.dumps(final_output, indent=2, sort_keys=True)


def analyse_cache(verbose=False):
    """
    Analyses cache: if one source contains entrie, how many else do?
    This needs alot of time.. Depends on ammount of entries and sources.
    Additionally, the value of this feature is not really high because
    there are max. 2 more entries on one queried item. Maybe for
    alot more sources and sql database.
    Iterates over source->entries->othersources->entriesofothersource
    :param verbose: Textoutput True/False
    :return:
    """

    appearsin_list = []

    # first, get all the cached data
    sources = sp.get_sources()
    all_cachedata = [0] * len(sources)
    for source in sources:
        iscached = source[8]
        sourceid = int(source[0])
        if iscached == "True":
            cachedata, _ = get_local_storage_info(sourceid)
        else:
            cachedata = []
        all_cachedata[sourceid - 1] = cachedata

    # second, compare cache entries
    # iterate over all cached sources
    for source in sources:
        sourceid = int(source[0])
        datatype = source[3]
        iscached = source[8]
        if verbose:
            print("Started comparing entries from source " + str(sourceid) +
                  " with " + str(len(all_cachedata[sourceid - 1])) + " entries.")

        if iscached == "True":
            # iterate over all other cache entries
            for entry in all_cachedata[sourceid - 1]:
                # print("Comparing source " + str(sourceid) + " with source " + str(cmpsourceid) + ".")
                appearsin = 0
                for cmpsource in sources:
                    cmpsourceid = int(cmpsource[0])
                    cmpiscached = cmpsource[8]
                    # find entries for same potential threat
                    if cmpiscached == "True" and len(all_cachedata[cmpsourceid - 1]) > 0 and cmpsourceid != sourceid:
                        for cmpentry in all_cachedata[cmpsourceid - 1]:
                            if datatype in cmpentry:
                                if entry[datatype] == cmpentry[datatype]:
                                    appearsin += 1
                                    all_cachedata[cmpsourceid - 1].remove(cmpentry)
                                    break

                appearsin_list.append(appearsin)
                if appearsin > 0:
                    if verbose:
                        print(entry[datatype] + " appears also in " + str(appearsin) + " more source/s.")
                all_cachedata[sourceid - 1].remove(entry)

    avg = float(sum(appearsin_list)) / float(len(appearsin_list))

    print ("Average appearance: " + str(avg))
    print ("Median: " + str(numpy.median(numpy.array(appearsin_list))))
    print ("Minimum: " + str(min(appearsin_list)))
    print ("Maximum: " + str(max(appearsin_list)))


def start_update_daemon(interval=3600, verbose=False):
    """
    :param interval: update interval in seconds, once every 60mins is fine, depends on amount of sources & entries
    :param verbose: Textoutput True/False
    :return:
    """
    threading.Timer(interval, start_update_daemon).start()
    update_local_storage(verbose=verbose)
    # analyse_cache(verbose=verbose)


# analyse_cache(verbose=False)
# update_local_storage(verbose=True)

""" ##### Begin of Confidence Rater #### """
# config
CR_DIR = 'confidence_rating/'
CR_DIR = '/'.join(path_of_executing_package) + '/' + CR_DIR


def _get_saved_confidence_ratings(filename="cr"):
    """
    if there does not exist data, it is created in the CR_DIR which is also be created if it does not exist
    :param identnr:
    :return: loaded json dict
    """

    conf_rat_dir = os.path.dirname(CR_DIR)
    path = CR_DIR + filename + '.json'

    if not os.path.exists(conf_rat_dir):
        os.makedirs(conf_rat_dir)
    if not os.path.isfile(path):
        new_file = _open_file(path, 'w')
        json.dump([], new_file)
        new_file.close()

    filehandle = _open_file(path, 'r')
    loaded = json.load(filehandle)
    filehandle.close()

    return loaded, path


def _map_response_time_to_scale(response_time_in_ms):
    # 1 if RT <= 100ms
    # between 1 and 0.5 if 100 < RT <= 1000ms
    # from 0.5 until 0 if 1000 < RT <= 10000ms
    # 0 else

    response_time_in_ms = float(response_time_in_ms)
    if response_time_in_ms <= 100:
        return 1.0

    elif 100 < response_time_in_ms <= 1000:
        return (0.5 - 1.0) / (1000.0 - 100.0) * (response_time_in_ms - 100.0) + 1

    elif 1000 < response_time_in_ms <= 10000:
        return (0.0 - 0.5) / (10000.0 - 1000.0) * (response_time_in_ms - 1000.0) + 0.5

    else:
        return 0


def _map_sample_information_content_to_scale(sample_information_content, mean_information_content):
    ratio = sample_information_content / mean_information_content
    if ratio >= 2:
        return 1.0
    elif 2 > ratio > 0:
        return sample_information_content / (2.0 * mean_information_content)
    else:
        return 0.0


def _map_factors_to_overall_rating(factors):
    """
    Sums up all factors (if not None) and returns the average of them (confidence rating)
    :type factors: array with factors
    """
    sum_factors = 0.0
    cnt = 0.0
    for factor in factors:
        if factor is not None:
            sum_factors += factor
            cnt += 1.0

    return sum_factors / cnt


def _get_information_amount(random_entry):
    cnt = 0
    for key in random_entry:
        if type(random_entry[key]) == dict or type(random_entry[key]) == list:
            if len(random_entry[key]) > 0:
                cnt += 1
        elif len(str(random_entry[key])) > 0:
            cnt += 1
    return cnt


def compute_confidence_ratings(verbose=False, logging=False):
    """
    Iterates over all sources to create a confidence rating based on several factors,
    which are computed for each source. Prepare yourself for confusing code.
    :param verbose: Textoutput true/False
    :return:
    """
    if verbose:
        print("Generating current Confidence Rating.")

    # get possible datatypes
    all_datatypes = []
    new_avgs = {}
    datatype_plugins = ph.get_plugins("datatype")
    for datatype_plugin in datatype_plugins:
        loaded_plugin = ph.load_plugin(datatype_plugin)
        all_datatypes.append(loaded_plugin.get_type_name())
        new_avgs[loaded_plugin.get_type_name()] = 0.0
    # load saved data
    saved_data, path = _get_saved_confidence_ratings()
    if logging:
        history, path_history = _get_saved_confidence_ratings(filename='cr_history')
        new_history = []
        if len(history) > 0:
            for entry in history:
                if entry["sourceid"] is None:
                    info_amount = entry
                    break
        else:
            info_amount = {"sourceid": None}
            for datatype in all_datatypes:
                info_amount[datatype] = []

    if len(saved_data) > 0:
        saved = True
    else:
        saved = False

    if saved:
        old_ratings_dict = saved_data[0]
        old_avgs = saved_data[1]

    # set up new data
    new_data = [[], {}]
    new_computed_avgs = {}
    for datatype in all_datatypes:
        new_computed_avgs[datatype] = 0.0

    # get list with sources to start the rating
    sources = sp.get_sources()
    for source in sources:

        # get transparency rating if set
        trans_rating = source[9]
        source_id = str(source[0])
        source_url = str(source[1])
        types_as_string = str(source[3])
        if logging:
            if len(history) > 0:
                for old_log_entry in history:
                    if old_log_entry["sourceid"] == source_id:
                        log_entry = old_log_entry
                        break
                    else:
                        log_entry = {"sourceid": source_id,
                                     "lambda1": [],
                                     "lambda2": [],
                                     "lambda3": []}
            else:
                log_entry = {"sourceid": source_id,
                             "lambda1": [],
                             "lambda2": [],
                             "lambda3": []}

        random_entries = {}
        source_types = []
        for datatype in types_as_string.split(','):
            source_types.append(datatype.strip())
        # print trans_rating
        if trans_rating == "None":
            lambda1 = None
        else:
            lambda1 = float(trans_rating)

        # analyze provided data of current source
        iscached = (source[8])
        if iscached == "True":
            iscached = True
        elif iscached == "False":
            iscached = False

        if iscached:
            data, _ = get_local_storage_info(source_id)
            random_entries[source_types[0]] = random.choice(data)
        else:
            """generated_list = [exrex.getone(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),  # ip
                                      exrex.getone(r'WWW\.(.+)\.[A-Z]{2,3}'),  # url
                                      exrex.getone(r'([a-fA-F\d]{32})')]  # hash"""
            for source_type in source_types:
                while True:
                    matching_random_source = random.choice(sp.get_sources(datatypes=source_type))
                    if matching_random_source[0] != source_id:
                        break
                random_entry = []
                if matching_random_source:
                    entries, _ = get_local_storage_info(matching_random_source[0])
                    if len(entries) > 0:
                        random_entry_cache = random.choice(entries)
                        data = str(random_entry_cache[matching_random_source[3]])
                        try:
                            random_entry = json.loads(fetch_data(source_id, lookedup_resource=data))
                        except Exception:
                            random_entry = []
                if len(random_entry) > 0:
                    random_entry = random_entry[0]
                else:
                    random_entry = []
                random_entries[source_type] = random_entry
        # count information filled keys
        for source_type in random_entries:
            random_entry = random_entries[source_type]
            if len(random_entry) > 0:
                cnt = _get_information_amount(random_entry)
                if logging:
                    info_amount[source_type].append(cnt)
                # check for saved average information content values
                avg_sum = 0.0
                datatype_cnt = 0.0
                if source_type in source_types:
                    if saved:
                        if old_avgs[source_type]:
                            avg_sum += old_avgs[source_type]
                    datatype_cnt += 1.0
                    new_computed_avgs[source_type] += cnt

                if saved:
                    mean = avg_sum / datatype_cnt
                else:
                    mean = cnt
                lambda2 = _map_sample_information_content_to_scale(cnt, mean)
            else:
                lambda2 = None

        # calculate response times and map to scale
        buff = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, source_url)
        c.setopt(c.WRITEDATA, buff)
        try:
            c.perform()
        except Exception:
            lambda3 = 0.0
        finally:
            if c.getinfo(c.RESPONSE_CODE) == 000:  # not available
                lambda3 = 0.0
            else:
                response_time = c.getinfo(c.TOTAL_TIME) * 100
                lambda3 = _map_response_time_to_scale(response_time)  # not yet, needs mapping
            c.close()

        new_cr = _map_factors_to_overall_rating([lambda1, lambda2, lambda3])
        avg_cr = new_cr

        if saved and old_ratings_dict:
            for source_entry in old_ratings_dict:
                if source_entry["sourceid"] == source_id:
                    iter_counter = source_entry["cnt"]
                    old_cr = source_entry["cr"]
                    # new stuff:
                    avg_cr = ((iter_counter * old_cr) + new_cr) / (iter_counter + 1)
                    # old stuff:
                    # avg_cr = (old_cr + new_cr) / 2.0
                    break
        else:
            iter_counter = 0
        iter_counter += 1
        new_data[0].append({"sourceid": str(source_id), "cr": avg_cr, "cnt": iter_counter})
        if logging:  # save new data
            log_entry["lambda1"].append(lambda1)
            log_entry["lambda2"].append(lambda2)
            log_entry["lambda3"].append(lambda3)
            new_history.append(log_entry)
        if verbose:
            print("Results for Source {}: lambda1: {}, lambda2: {}, lambda3: {}. New Rating: {}".format(
                source_id, lambda1, lambda2, lambda3, avg_cr))

    for datatype in new_avgs:
        amount_of_sources_with_that_type = float(len(sp.get_sources(datatypes=datatype)))
        new_avgs[datatype] = new_computed_avgs[datatype] / amount_of_sources_with_that_type
    new_data[1] = new_avgs

    filehandle_write = _open_file(path, 'w')
    json.dump(new_data, filehandle_write, indent=2, sort_keys=True)
    filehandle_write.close()
    if logging:
        new_history.append(info_amount)
        filehandle_write = _open_file(path_history, 'w')
        json.dump(new_history, filehandle_write, indent=2, sort_keys=True)
        filehandle_write.close()
    print("Rating iteration done.")
    return json.dumps(new_data, indent=True, sort_keys=True)


def start_rating_daemon(interval=120, verbose=False):
    """
    :param interval: analyze interval in seconds, once every 30mins is fine, depends on amount of sources & entries
    :param verbose: Textoutput True/False
    :return:
    """
    threading.Timer(interval, start_rating_daemon).start()
    compute_confidence_ratings(verbose=verbose, logging=False)


def get_confidence_rating(sourceid):
    sourceid = str(sourceid)
    loaded, _ = _get_saved_confidence_ratings()
    for entry in loaded[0]:
        if entry['sourceid'] == sourceid:
            confidence_rating = entry['cr']
            return confidence_rating


def plot_history():
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Matplotlib / numpy not found.")
        return False

    history, _ = _get_saved_confidence_ratings("cr_history")
    all_ratings = []
    iterations = 0
    which_sources = ["1", "6", "7", "12", "13", "15", "16"]
    for entry in history:
        if entry["sourceid"] in which_sources:
            l1 = entry["lambda1"]
            l2 = entry["lambda2"]
            l3 = entry["lambda3"]
            cr = []
            if len(l1) != len(l2) != len(l3):
                print("Error in Log. Can't handle different sizes.")
                return False
            else:
                iterations = len(l1)
                for i in range(iterations):
                    # if entry["sourceid"] == "12":
                    #     new_rating = _map_factors_to_overall_rating([l1[i], l2[i], l3[i]])
                    # else:
                    new_rating = _map_factors_to_overall_rating([None, l2[i], l3[i]])

                    if i == 0:
                        rating = new_rating
                    else:
                        rating = (i * cr[i-1] + new_rating) / (i + 1)
                        # rating = (new_rating + cr[i-1])/2
                    cr.append(rating)
                avg = sum(cr)/len(cr)
                print(cr[i])
            all_ratings.append(cr)

    # plotting
    t = np.arange(1, iterations + 1, 1)
    cnt = 0

    ax = plt.subplot()
    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                     ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(25)
    for source in all_ratings:
        ident = which_sources[cnt]
        source_info = sp.get_sources(ident=ident)[0]
        plt.plot(t, source, '-', label=source_info[1], linewidth=2.0)
        cnt += 1
    plt.xlabel('Iterationen')
    plt.ylabel('Confidence Rating')
    plt.grid(True)
    plt.axis([1, iterations, 0, 1.])
    plt.legend(loc='lower center',  # bbox_to_anchor=(0.5, 1.05),
               ncol=3, fancybox=True, shadow=True, prop={'size': 25})
    plt.show()
