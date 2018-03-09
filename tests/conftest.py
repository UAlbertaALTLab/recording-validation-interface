#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import sys
from pathlib import Path

import pytest  # type: ignore
from pytest_flask.fixtures import LiveServer  # type: ignore


# XXX: gross sys.path manipulation to allow us to
# `import recval` from within the tests
sys.path.append(
    # .parent == ./
    # .parent.parent == ../
    str(Path(__file__).parent.parent.resolve())
)


@pytest.fixture
def app():
    """
    The Flask app. Required by pytest-flask.
    """

    from recval.app import app
    return app


# my_live_server code adpated from https://github.com/pytest-dev/pytest-flask/blob/master/pytest_flask/fixtures.py

# The MIT License (MIT)
#
# Copyright © 2014–2016 Vital Kudzelka and contributors.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


@pytest.fixture(scope='function')
def my_live_server(request, app, monkeypatch):
    """Run application in a separate process.

    When the ``live_server`` fixture is applyed, the ``url_for`` function
    works as expected::

        def test_server_is_up_and_running(live_server):
            index_url = url_for('index', _external=True)
            assert index_url == 'http://localhost:5000/'
            res = urllib2.urlopen(index_url)
            assert res.code == 200

    """
    # Get an open port. There's technically a race condition here, but
    # whatever.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()

    # Explicitly set application ``SERVER_NAME`` for test suite
    # and restore original value on test teardown.
    server_name = app.config['SERVER_NAME'] or 'localhost'
    monkeypatch.setitem(app.config, 'SERVER_NAME',
                        _rewrite_server_name(server_name, str(port)))

    server = LiveServer(app, port)
    server.start()
    yield server
    server.stop()


def _rewrite_server_name(server_name, new_port):
    """Rewrite server port in ``server_name`` with ``new_port`` value."""
    sep = ':'
    if sep in server_name:
        server_name, port = server_name.split(sep, 1)
    return sep.join((server_name, new_port))
