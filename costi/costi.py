# -*- coding: utf-8 -*-
try:
    import argparse
    import sys
    import web
    from web import form
    import json
    import costi_api
    import inspect
except ImportError:
    raise ImportError('Missing dependencies, please check readme.')


path_of_executing_costi_py = inspect.stack()[0][1].split('/')
path_of_executing_package = path_of_executing_costi_py[0:len(path_of_executing_costi_py)-1]
path_of_executing_package = '/'.join(path_of_executing_package) + '/'

render = web.template.render(path_of_executing_package + 'templates/', base='')

urls = (
    '/(.*)',
    'index'
)

search_form = form.Form(
    form.Textbox(name="searchbar"),  # , value="192.168.0.1"),
    # form.Dropdown(name="datatype", args=costi_api.get_all_data_types()),
    form.Button("Find", type="submit", description="Find")

)


class index:
    def GET(self, item):
        f = search_form()
        # print search_form.render()
        get = web.input(datatype=None)

        if item and get:  # unsecure but works..
            output = costi_api.lookup(item)
            return render.index(costi_api.json_to_html(output))

        else:
            return render.index(f.render())

    def POST(self, item):
        f = search_form()
        if not f.validates():
            return render.formtest(f)
        else:
            if len(f.d.searchbar) > 0:
                output = costi_api.lookup(f.d.searchbar)
                return render.index(costi_api.json_to_html(output))
            else:
                return render.index("Searchfield empty.")


def parse_arguments():
    parser = argparse.ArgumentParser(description='Costi - Collection of Open Source Threat Intelligence')
    parser.add_argument('-p', action="store", dest='port', default='8080',
                        help='Port for webinterface.')

    return parser.parse_args()


def main():
    # arguments = parse_arguments()

    app = web.application(urls, globals())
    print 'Starting daemons for updating the cache and confidence rating..'
    costi_api.start_update_daemon()
    costi_api.start_rating_daemon()
    print 'Start server..'
    app.run()


if __name__ == "__main__":
    main()
