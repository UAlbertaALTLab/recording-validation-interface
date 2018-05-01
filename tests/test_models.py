#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import tempfile
from pathlib import Path

import pytest  # type: ignore
from sqlalchemy.schema import MetaData, DropConstraint  # type: ignore
from sqlalchemy.exc import SQLAlchemyError  # type: ignore

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


def test_insert_recording_twice(db):
    """
    Insert the exact SAME recording twice should fail.
    """

    word = Word(transcription='acimosis', translation='puppy')

    # Insert it once.
    rec1 = Recording.new(phrase=word, input_file=TEST_WAV, speaker='NIL')
    db.session.add(rec1)
    db.session.commit()

    # Insert it again.
    rec2 = Recording.new(phrase=word, input_file=TEST_WAV, speaker='NIL')
    db.session.add(rec1)
    with pytest.raises(SQLAlchemyError):
        db.session.commit()


def test_transcription_history(db):
    word = Word(transcription='\n aci\u0302mosis \r', translation='puppy')
    recording = Recording.new(phrase=word, input_file=TEST_WAV, speaker='NIL')
    # Insert it for the first time.
    db.session.add(recording)
    db.session.commit()
    word_id = word.id
    del word

    # In another instance, fetch the word.
    word = Word.query.filter(Word.id == word_id).one()
    assert word.transcription == 'ac\u00EEmosis'  # acîmosis

    # Now change it. For example, remove the circumflex.
    word.update('transcription', 'acimosis')
    db.session.commit()
    del word

    # Fetch it one more time, and check that it has changed.
    word = Word.query.filter(Word.id == word_id).one()
    assert word.transcription == 'acimosis'


@pytest.fixture()
def app():
    with _app.app_context():
        yield _app


@pytest.fixture()
def db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///:memory:'

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
