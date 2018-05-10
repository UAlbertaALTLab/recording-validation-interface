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
        # Ensure the app does not allow us to do this without logging in.
        assert rv.status_code in (302, 401, 403, 404)


# TODO: create users, and login as them

@pytest.mark.skip
def test_login(app, client):
    """
    """
    with app.test_request_context():
        rv = client.get(url_for('list_phrases', page=1))
        assert 200 == rv.status_code


def test_database_has_bot_user(db):
    """
    There should be one bot user, the importer.
    It should have the importer role.
    """
    from recval.model import user_datastore
    importer = user_datastore.find_user(email='importer@localhost')
    assert importer is not None
    assert importer.has_role('<importer>')


def test_cannot_login_as_importer(client, app):
    """
    It should be IMPOSSIBLE to login as the importer!
    """
    from recval.model import user_datastore

    # The password should be unset...
    importer = user_datastore.find_user(email='importer@localhost')
    assert importer.password is None

    # Additionally, logging in should not work.
    with app.test_request_context():
        rv = client.post(url_for('security.login'),
                         follow_redirects=True,
                         data=dict(
                             email='importer@localhost',
                             password=''
                         ))
        # TODO: Create a more robust test :/
        assert b'Password not provided' in rv.data


def json_body(**kwargs) -> bytes:
    """
    Create a JSON body, for sending as a request body to an endpoint.
    """
    import json
    return json.dumps(dict(**kwargs)).encode('UTF-8')
