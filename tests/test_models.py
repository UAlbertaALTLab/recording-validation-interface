#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

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
    Insert the exact SAME recording twice; the second should fail.
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


def test_transcription_update(db):
    """
    Ensure that a word's transcription can be changed.
    """

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


def test_translation_history(db):
    """
    Checks that the translation has a history, and that updating the
    translation updates the history.
    """

    word = Word(transcription='acîmosis', translation=' puppy  ')
    recording = Recording.new(phrase=word, input_file=TEST_WAV, speaker='NIL')
    # Insert it for the first time.
    db.session.add(recording)
    db.session.commit()
    word_id = word.id
    del word

    # In another instance, fetch the word.
    word = Word.query.filter(Word.id == word_id).one()
    assert word.translation == 'puppy'

    # Now, check its history.
    assert word.translation_meta.is_root
    assert len(word.translation_history) == 1

    # Now, update it!
    word.translation = 'many doggos'
    db.session.commit()
    del word

    # Refetch it.
    word = Word.query.filter_by(id=word_id).one()
    assert word.translation == 'many doggos'

    assert not word.translation_meta.is_root
    assert len(word.translation_history) == 2


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
    """
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
