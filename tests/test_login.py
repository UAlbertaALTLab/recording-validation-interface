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


@pytest.mark.skip
def test_login(app, client, db):
    """
    Test logging in as users.
    """
    from datetime import datetime
    from flask_security import current_user

    user1 = user_datastore.create_user(
        email='user1@example.com',
        password='password123',
        active=True,
        confirmed_at=datetime.utcnow(),
    )
    db.session.commit()

    with app.test_request_context():
        with client:
            rv = client.post(url_for('security.login'), data=dict(
                email='user1@example.com',
                password='password123'
            ))
            assert current_user.username == 'user1'


def test_database_has_bot_user(db):
    """
    There should be one bot user, the importer.
    It should have the importer role.
    """
    from recval.database import importer
    assert importer.has_role('<importer>')


def test_cannot_login_as_importer(client, app):
    """
    It should be IMPOSSIBLE to login as the importer!
    """
    from recval.database import importer

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


@pytest.mark.skip(reason="It's hard to test logging in...")
def test_validator_can_change_transcriptions(app, client, acimosis, validator):
    """
    Tests that validators are allowed to change transcriptions.
    """

    with app.test_request_context(), client:
        rv = client.patch(
            url_for('update_text', phrase_id=acimosis),
            data=json_body(field='translation',
                           value='pup pup'),
            content_type='application/json'
        )
        assert rv.status_code == 204, rv.data.decode('UTF-8')


def json_body(**kwargs) -> bytes:
    """
    Create a JSON body, for sending as a request body to an endpoint.
    """
    import json
    return json.dumps(dict(**kwargs)).encode('UTF-8')


@pytest.fixture
def user_datastore():
    from recval.model import user_datastore
    return user_datastore


@pytest.fixture
def validator(user_datastore):
    """
    A user that has validation privledges.
    """
    from datetime import datetime
    from flask_security import current_user
    validator_role = user_datastore.find_role('validator')
    assert validator_role is not None
    return user_datastore.create_user(
        email='validator@localhost',
        password=None,
        active=True,
        confirmed_at=datetime.utcnow(),
        roles=[validator_role]
    )
