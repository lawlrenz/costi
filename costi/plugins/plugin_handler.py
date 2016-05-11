# -*- coding: utf-8 -*-

try:
    import imp
    import os
    import inspect
except ImportError:
    raise ImportError('Missing dependencies, please check readme.')


def get_plugins(plugintype, pluginname=""):
    # returns list of plugininformation which can be used to load_plugin
    path_of_executing_pluginhandler_py = inspect.stack()[0][1].split('/')
    path_of_executing_package = path_of_executing_pluginhandler_py[0:len(path_of_executing_pluginhandler_py) - 1]
    pluginfolder = '/'.join(path_of_executing_package) + '/' + plugintype

    plugins = []
    possibleplugins = os.listdir(pluginfolder)
    validplugins = []

    # filter for .py files
    for pluginnum in range(len(possibleplugins)):

        ending = possibleplugins[pluginnum].split(".")[1]
        if ending == "py":
            validplugins.append(possibleplugins[pluginnum])

    # return valid plugins
    for plugin in validplugins:
        tmppluginname = plugin[0:len(plugin)-3]
        if pluginname == "" or tmppluginname.split("_")[1] == pluginname:  # remove prefix and ending
            infos = [tmppluginname]
            try:
                tmp = imp.find_module(tmppluginname, [pluginfolder])
            except ImportError:
                print('Can not load Plugin.')

            for i in range(len(tmp)):
                infos.append(tmp[i])
            plugins.append(infos)
    return plugins


def load_plugin(plugininfos):
    # loads plugin an returns as module
    return imp.load_module(plugininfos[0], plugininfos[1], plugininfos[2], plugininfos[3])

