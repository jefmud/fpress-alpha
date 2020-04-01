# a simple runner for FPRESS
from fpress import app
from fpress.utils import cli_arg_value, cli_arg_exists


# can override the project config (from fpress/app.cfg) HOST and PORT
# EXAMPLE:
#    $ python run.py --host 0.0.0.0 --port 8080 --deploy
#
# Notes on port/host
# --port 5000 is typical, --port 80 or --port 8080 are traditional public facing
# --host 127.0.0.1 is for local development and can only be seen on your computer
# --host 0.0.0.0 is wide open but external visibility depends on your firewall/router
# --deploy flag runs the greenlet server
if __name__ == '__main__':
    # by default it will be a local application run on port 5000
    PORT = cli_arg_value('--port', default=app.config['PORT'])
    HOST = cli_arg_value('--host', default=app.config['HOST'])

    if cli_arg_exists('--deploy'):
        # deploy as a "greenlet"
        # it can stand alone reasonably safely/stable,
        # but ideally will be proxied behind Nginx or Apache for production
        from gevent.pywsgi import WSGIServer
        print("Greenlet server starting on host={} port={}".format(HOST, PORT))
        http_server = WSGIServer((HOST, PORT), app)  # launch a GEvent server
        http_server.serve_forever()
    else:
        # use Flask Development server
        app.run(host=HOST, port=PORT, debug=app.config['DEBUG'])
