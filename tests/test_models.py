#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import tempfile
from pathlib import Path

import pytest  # type: ignore
from sqlalchemy.schema import MetaData, DropConstraint  # type: ignore

from recval.model import Word, Sentence, Recording
from recval.model import db as _db
from recval.app import app as _app


TEST_WAV = Path(__file__).parent / 'fixtures' / 'test.wav'
assert TEST_WAV.exists()

# Based on http://alextechrants.blogspot.ca/2014/01/unit-testing-sqlalchemy-apps-part-2.html


def test_insert_word(db):
    """
    Insert a word, and retrieve it again.
    """

    word = Word(transcription=' acimosis', translation='puppy ')
    recording = Recording.new(phrase=word, input_file=TEST_WAV, speaker='NIL')
    db.session.add(recording)
    db.session.commit()

    result_set = Word.query.filter(Word.translation == 'puppy').all()
    assert len(result_set) >= 1
    assert word in result_set

    result_set = Word.query.filter(Word.transcription == 'acimosis').all()
    assert len(result_set) >= 1
    assert word in result_set


@pytest.fixture()
def app():
    with _app.app_context():
        yield _app


@pytest.fixture()
def db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///:memory:'

    _db.create_all()
    _db.session.flush()
    _db.session.expunge_all()
    _db.session.commit()

    yield _db

    _db.session.close()
