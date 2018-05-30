#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import re
import pytest  # type: ignore


def test_index(mock_server):
    """
    The index should redirect to the phrase page.
    """
    r = mock_server.get('/')
    assert r.status_code == 200
    assert 'Maskwacîs Recording' in r.text


def test_login(mock_server, db, user_datastore, url_for):
    """
    Test logging in as users.
    """
    from datetime import datetime
    from flask_security import current_user  # type: ignore

    email = 'user1@example.com'
    password = 'password123'

    # Create a user
    user1 = user_datastore.create_user(
        email=email,
        password=password,
        active=True,
        confirmed_at=datetime.utcnow(),
    )
    db.session.commit()

    from recval.model import User
    assert any(u.email == email for u in User.query.all())

    # Go to the index page, not logged in.
    r = mock_server.get('/')
    assert email not in r.text

    r = mock_server.get(url_for('security.login'))
    csrf_token = get_csrf_token(r.text)

    # Login as the user we just created.
    r = mock_server.post(url_for('security.login'), data=dict(
        email=email, password=password, csrf_token=csrf_token,
        next=""
    ))
    # XXX: Checks for the the Bootstrap error message class,
    # because Flask-Security doesn't know how to HTTP status code.
    assert 'alert-danger' not in r.text

    # Navigate back to the homepage.
    r = mock_server.get('/')
    assert email in r.text


def get_csrf_token(html: str) -> str:
    """
    Really hacky way of getting the CSRF token from a page.
    Assumes the CRSF token is in the HTML in an <input> element ALL ON ONE
    LINE! e.g.,

        <input type="hidden" name="csrf_token" value="..." />
    """
    m = re.search(r'<input.+name="csrf_token".+value="([^"]+)"', html)
    if m is None:
        raise ValueError("Could not find CRSF token in HTML: " + html)
    return m.group(1)
