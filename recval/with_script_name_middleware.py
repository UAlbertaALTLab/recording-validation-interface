#!/usr/bin/env python3.6

# Copyright (C) 2018 Eddie Antonio Santos <easantos@ualberta.ca>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Wraps recval.app.app in WSGI middleware that sets the server name (path
prefix) to whatever is in the FLASK_SCRIPT_NAME environment variable.

Usage:

In .env, write this:

    export FLASK_SCRIPT_NAME=/script/name/for/your/app
    export FLASK_APP=recval.with_script_name_middleware:create_app

For example, if the server is NOT running as the root host, but rather is
running as a "subdirectory", e.g.,

It's running as:

    example.com/validation/

Instead of:

    validation.example.com/

Use this middleware to set the subdirectory as:

FLASK_SCRIPT_NAME=/validation

Based on: https://gist.github.com/Larivact/1ee3bad0e53b2e2c4e40
"""

import sys
from os import environ as env
from recval.app import app as _app


def script_name_middleware(app):
    """
    WSGI Middleware that appends a script root.
    """

    try:
        SCRIPT_NAME = env['FLASK_SCRIPT_NAME']
    except KeyError:
        raise RuntimeError(
            "Did not provide FLASK_SCRIPT_NAME in the environment!\n"
            "Usage:\n"
            "     export FLASK_SCRIPT_NAME=/your-path-prefix\n"
            "     export FLASK_APP=recval.with_script_name_middleware:create_app\n"
            "     flask run\n"
        )

    def application(environ, start_response):
        if environ['PATH_INFO'].startswith(SCRIPT_NAME):
            # Take out the script name from the path info
            environ['PATH_INFO'] = environ['PATH_INFO'][len(SCRIPT_NAME):]
        environ['SCRIPT_NAME'] = SCRIPT_NAME

        return app(environ, start_response)

    return application


def create_app():
    _app.wsgi_app = script_name_middleware(_app.wsgi_app)
    return _app
