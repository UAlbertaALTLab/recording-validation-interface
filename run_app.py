#!/usr/bin/env python3.6
"""
WSGI middleware that sets the server name (path prefix) to whatever is in the
WSGI_SCRIPT_NAME environment variable.

Based on: https://gist.github.com/Larivact/1ee3bad0e53b2e2c4e40
"""

import sys
from os import environ as env
from werkzeug.serving import run_simple
from recval.app import app as wrapped_application


try:
    SCRIPT_NAME = env['FLASK_SCRIPT_NAME']
except KeyError:
    print("Did not provide FLASK_SCRIPT_NAME in the environment!\n"
          "Usage:\n"
          "     export FLASK_SCRIPT_NAME=/your-path-prefix\n"
          "     python3.6 run_app.py\n",
          file=sys.stderr)
    sys.exit(1)


def app(environ, start_response):
    """
    WSGI Middleware that appends a script root.
    """
    if environ['PATH_INFO'].startswith(SCRIPT_NAME):
        # Take out the script name from the path info
        environ['PATH_INFO'] = environ['PATH_INFO'][len(SCRIPT_NAME):]
    environ['SCRIPT_NAME'] = SCRIPT_NAME
    return wrapped_application(environ, start_response)


if __name__ == '__main__':
    # Listens to the loopback interface on port 5000.
    # Intended for reverse proxying.
    run_simple('127.0.0.1', 5000, app, use_reloader=True)
