# -*- coding: utf-8 -*-
try:
    import costi_sourcepool as sp
    import plugins.plugin_handler as ph
    import costi_cache as cache
    import json
    import datetime
    import pygal
    from pygal.style import Style
except ImportError:
    raise ImportError('Missing dependencies, please check readme.')


def lookup(searchbar_input, datatypes=None, tags=None):
    # queries sources for information and returns them in json format
    return cache.query(searchbar_input, datatypes=datatypes, tags=tags)


def add_source(provider, link, data_type, fetcher, caching, tag="", description="", update_type="a"):
    # adds source to your source list.csv
    # returns true if success or false if failed (e.g. source exists allready, parser does not exist)
    return sp.add_source(provider, link, data_type, tag, description, fetcher, update_type, caching)


def rm_source(source_id):
    # rm source with source_id from your sources.csv and all the data from the cache
    return sp.rm_source(source_id)


def get_sources(datatypes):
    # returns a list with all sources for that types/type or all types
    return sp.get_sources(datatypes)


def get_all_data_types():
    # returns a list with all available types like ['hash', 'ip', ...]
    data_type_names = []
    all_types = ph.get_plugins("datatype")
    for data_type in all_types:
        loadedtype = ph.load_plugin(data_type)
        data_type_names.append(loadedtype.get_type_name())
    return data_type_names


def update_cache(source_id=None, verbose=False):
    return cache.update_local_storage(source_id, verbose=verbose)


def start_update_daemon(interval=3600, verbose=False):
    cache.start_update_daemon(interval=interval, verbose=verbose)


def start_rating_daemon(interval=300, verbose=False):
    cache.start_rating_daemon(interval=interval, verbose=verbose)


def json_to_html(jsonoutput):
    jsonoutput_loaded = json.loads(jsonoutput)
    html = ""

    if len(jsonoutput_loaded[1]) >= 1:

        # build piechart
        custom_style = Style(
          background='transparent',
          font_family='sans-serif',
          label_font_size=50,
          legend_font_size=25,
          tooltip_font_size=25,
          plot_background='transparent',
          foreground='#FFF',
          foreground_strong='#FFF',
          foreground_subtle='#FFF',
          opacity='.6',
          opacity_hover='0.8',
          transition='400ms ease-in',
          colors=('#FFF', '#FFF', '#FFF')
          )

        pie_chart = pygal.Pie(half_pie=True, style=custom_style, show_legend=False,  # legend_at_bottom=True, legend_at_bottom_columns=3,
                              margin=0, legend_box_size=40)

        # add statistics
        html += "<table class=res><caption>Statistics</caption>"
        for info in jsonoutput_loaded[0]:
            if "Queried Sources" in info:
                for item in info:
                    if item == "Positives":
                        pie_chart.add(item, [{'value': int(info[item]), 'color': '#F00'}])
                    elif item == "Negatives":
                        pie_chart.add(item, [{'value': int(info[item]), 'color': '#0F0'}])
                    elif item == "Unclear":
                        pie_chart.add(item, [{'value': int(info[item]), 'color': '#FF0'}])
                    else:
                        html += "<tr><td class=cat>" + item + "</td><td class=cont>" \
                                + str(info[item]) + "</td></tr>"
            elif "ressource" in info:
                for item in info:
                    html += "<tr><td class=cat>Queried Ressource</td><td class=cont>" + str(info[item]) + "</td></tr>"
            else:
                html += "<tr><td class=cat>Scores</td><td><table class=scoring><tr>" \
                        "<td class=cat><strong>Tag<strong></td><td class=cont><strong>Score</strong></td></tr>"
                for action in info:
                    html += "<tr><td class=cat>" + str(action) + "</td><td class=cont>" + str(info[action]) + "</td></tr>"
                html += "</table><i><small>(Confidence Rating of the sources" \
                        " times Threatlevel summed up for each Tag)</small></i></td></tr>"
        html += "<tr><td class=cat>Visualization</td><td class=cont><div class=piechart>" \
                + pie_chart.render(is_unicode=True) + "</div></td></tr>"
        html += "</table>"

        # append html output built from json output
        for source in jsonoutput_loaded[1]:
            for hostname in source:
                hostname = hostname.encode('utf-8')
                html += "<table class=res><caption>" + hostname + "</caption>"
                entry_cnt = 1
                for entry in source[hostname]:
                    html += "<thead><tr><td>#" + str(entry_cnt) + "</td><td> &nbsp; </td></tr></thead><tbody>"
                    for info in entry:
                        if len(str(entry[info])) != 0:
                            content = str(entry[info])
                            if info == "date":
                                content = str(datetime.date.fromtimestamp(float(content)))

                            # uncool renaming, still prettier output though
                            if info == "date":
                                info = "Date of data retrieval"
                            elif info == "filename":
                                info = "Filename"
                            elif info == "sha1":
                                info = "SHA1"
                            elif info == "md5":
                                info = "MD5"
                            elif info == "sha256":
                                info = "SHA256"
                            elif info == "ip":
                                info = "IP"
                            elif info == "malicious":
                                info = "Threatlevel"
                            elif info == "url":
                                info = "URL"
                            elif info == "resolutions":
                                info = "Past IP resolutions"
                            elif info == "malware_type":
                                info = "Description"
                            elif info == "link":
                                info = "Link"
                            elif info == "status":
                                info = "Status"
                            elif info == "tag":
                                info = "Tags"
                            elif info == "scans":
                                info = "Verbose results"
                            html += "<tr><td class=cat>" + info + "</td><td class=cont>"

                            if info == "Filename" or info == "SHA1" or info == "MD5"\
                                    or info == "SHA256" or info == "IP" or info == "URL":
                                html += "<a href=" + content + ">" + content + "</a>"
                            elif info == "Tags":
                                for tag in content.split(','):
                                    stripped = tag.strip()
                                    html += "<a href=" + stripped + ">" + stripped + "</a> "
                            elif info == "Threatlevel":
                                if float(content) == 0:
                                    html += "<div class=nmal>"
                                elif float(content) == 100:
                                    html += "<div class=mal>"
                                else:
                                    html += "<div class=mmal>"
                                html += str(content) + "</div>"

                            # this is made for virustotal, but can also be used for similar things
                            elif info == "Verbose results":
                                scandict = entry["scans"]
                                html += "<ul>"
                                for key in scandict:
                                    html += "<li>" + str(key) + "<ul>"
                                    for subkey in scandict[key]:
                                        html += "<li>" + str(subkey) + ": " + str(scandict[key][subkey]) + "</li>"
                                    html += "</ul></li>"
                                html += "</ul>"
                            else:
                                html += content

                            html += "</td></tr>"
                    entry_cnt += 1
                    html += "<tr><td>&nbsp;</td><td>&nbsp;</td></tr></tbody>"
                html += "</table>"
    else:
        html += "<strong>No Data has been found. You can add more sources to improve effectivity.</strong>"
    return html
