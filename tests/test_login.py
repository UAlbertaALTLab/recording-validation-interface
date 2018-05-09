#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import pytest  # type: ignore
from flask import url_for  # type: ignore


def test_unauthenticated(client):
    """
    Going to the index page should give us a valid webpage.
    """
    rv = client.get('/', follow_redirects=True)
    assert 200 == rv.status_code


@pytest.mark.skip
def test_login(app, client):
    with app.test_request_context():
        rv = client.get(url_for('list_phrases', page=1))
        assert 200 == rv.status_code
