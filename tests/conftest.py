#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import pytest  # type: ignore
from recval.model import db as _db
from recval.app import app as _app, user_datastore


@pytest.fixture()
def app():
    """
    Yield an active Flask app context.
    """
    with _app.app_context():
        yield _app


@pytest.fixture()
def db(app):
    """
    Yields a database object bound to an active app context.
    The database starts empty, and is cleared of all data at the end of the
    test.

    Based on http://alextechrants.blogspot.ca/2014/01/unit-testing-sqlalchemy-apps-part-2.html
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///:memory:'

    # TODO: place audio in temporary directory.

    # Setup the database.
    _db.create_all()
    _db.session.flush()
    _db.session.expunge_all()
    _db.session.commit()

    yield _db

    # Tear down the database.
    _db.session.rollback()
    _db.drop_all()
    _db.session.flush()
    _db.session.expunge_all()
