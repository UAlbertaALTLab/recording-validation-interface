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


def test_change_string_unauthenticated(app, client, acimosis):
    """
    Trying to change a transcription or translation unvalidated should be an
    error.
    """
    with app.test_request_context():
        rv = client.patch(
            url_for('update_text', phrase_id=1),
            data=json_body(field='translation',
                           value='pup pup'),
            content_type='application/json'
        )
        print(rv.headers['location'])
        # Ensure the app does not allow us to do this without logging in.
        assert rv.status_code in (401, 403, 404)


@pytest.mark.skip
def test_login(app, client):
    """
    """
    with app.test_request_context():
        rv = client.get(url_for('list_phrases', page=1))
        assert 200 == rv.status_code


def json_body(**kwargs) -> bytes:
    import json
    return json.dumps(dict(**kwargs)).encode('UTF-8')
