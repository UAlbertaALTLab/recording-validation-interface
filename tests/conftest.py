#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from datetime import datetime
from pathlib import Path

import pytest  # type: ignore
from flask_security import current_user  # type: ignore


@pytest.fixture()
def app():
    """
    Yield an active Flask app context.
    """
    from recval.app import app as _app
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
    from recval.database import init_db
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///:memory:'

    # TODO: place audio in temporary directory.

    # Setup the database.
    db = init_db()
    db.session.flush()
    db.session.expunge_all()
    db.session.commit()

    yield db

    # Tear down the database.
    db.session.rollback()
    db.drop_all()
    db.session.flush()
    db.session.expunge_all()


@pytest.fixture()
def client(app, db):
    yield app.test_client()


@pytest.fixture()
def acimosis(db, wave_file_path):
    """
    Inserts the word 'acimosis'/'puppy' into the database.

    Returns the phrase.id of the inserted phrase.
    """
    from recval.model import Word, Recording
    word = Word(transcription='acîmosis', translation=' puppy  ')
    recording = Recording.new(phrase=word,
                              fingerprint='acimosis',
                              input_file=wave_file_path,
                              speaker='NIL')
    # Insert it for the first time.
    db.session.add(recording)
    db.session.commit()
    return word.id


@pytest.fixture()
def wave_file_path():
    """
    A recording saying "acimosis" (puppy), for use in test cases.
    """
    test_wav = Path(__file__).parent / 'fixtures' / 'test.wav'
    assert test_wav.exists()
    return test_wav


@pytest.fixture
def validator(user_datastore):
    """
    A user that has validation privledges.
    """
    validator_role = user_datastore.find_role('validator')
    assert validator_role is not None
    return user_datastore.create_user(
        email='validator@localhost',
        password=None,
        active=True,
        confirmed_at=datetime.utcnow(),
        roles=[validator_role]
    )


@pytest.fixture
def user_datastore():
    from recval.model import user_datastore
    return user_datastore
