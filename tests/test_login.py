#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

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

import pytest  # type: ignore
from flask import url_for  # type: ignore

from recval.database import special_users


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


def test_roles(db) -> None:
    """
    A fresh database should have at miniumum, these roles:

     - validator
     - community

    """
    from recval.model import Role
    roles = set(r.name for r in Role.query.all())

    assert {'validator', 'community'}.issubset(roles)


def test_database_has_bot_user(db):
    """
    There should be one bot user, the importer.
    It should have the importer role.
    """
    assert special_users.importer.has_role('<importer>')


def test_cannot_login_as_importer(client, app):
    """
    It should be IMPOSSIBLE to login as the importer!
    """

    assert special_users.importer.password is None

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
