#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import tempfile
from pathlib import Path

import pytest  # type: ignore
from sqlalchemy.schema import MetaData, DropConstraint  # type: ignore
from sqlalchemy.exc import SQLAlchemyError  # type: ignore

from recval.model import Phrase, Word, Sentence, Recording, VersionedString
from recval.model import RecordingQuality, ElicitationOrigin
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


def test_translation_history(db, acimosis):
    """
    Checks that the translation has a history, and that updating the
    translation updates the history.
    """

    # Fetch the word.
    word = Word.query.filter(Word.id == acimosis).one()
    assert word.translation == 'puppy'

    # Now, check its history.
    assert word.translation_meta.is_root
    assert len(word.translation_history) == 1

    # Now, update it!
    word.translation = 'smol doggo'
    db.session.commit()
    del word

    # Refetch it.
    word = Word.query.filter_by(id=acimosis).one()
    assert word.translation == 'smol doggo'

    # Get the entire translation history.
    assert not word.translation_meta.is_root
    assert len(word.translation_history) == 2

    # Update it back to the original. It should create a NEW entry.
    word.translation = 'puppy'
    db.session.commit()
    del word

    # Fetch it one last time.
    word = Word.query.filter_by(id=acimosis).one()
    # It should be back to puppy.
    assert word.translation == 'puppy'
    assert not word.translation_meta.is_root
    assert len(word.translation_history) == 3


def test_mark_recordings(db, acimosis):
    """
    Tests the ability to mark recordings as clean/unusable.
    """
    # Fetch the word.
    word = Word.query.filter(Word.id == acimosis).one()
    recording = next(iter(word.recordings))
    rec_id = recording.fingerprint
    assert recording.quality is None

    # Update it...
    recording.quality = RecordingQuality.clean
    db.session.commit()
    del word
    del recording

    # And make sure it has changed.
    recording = Recording.query.filter_by(fingerprint=rec_id).one()
    assert recording.quality == RecordingQuality.clean


def test_mark_word_source(db, acimosis):
    """
    Test marking the word with its source:
     - Maskwacîs dictionary
     - Rapid words
    """
    phrase = Phrase.query.filter_by(id=acimosis).one()
    assert phrase.origin is None

    phrase.origin = ElicitationOrigin.maskwacîs
    db.session.commit()
    del phrase

    phrase = Phrase.query.filter_by(id=acimosis).one()
    assert phrase.origin == ElicitationOrigin.maskwacîs


def test_search_by_transcription(db, acimosis):
    """
    Test adding a new phrase that does not have the same transcription.
    """
    initial_results = Phrase.query.all()
    assert len(initial_results) == 1
    assert initial_results[0].transcription != 'acimosisak'
    del initial_results

    word = Word(transcription='acimosisak', translation='litter of pups')
    db.session.add(word)
    db.session.commit()
    del word

    results = Phrase.query.all()
    assert len(results) == 2
    del results

    results = Phrase.query.filter(
        Phrase.transcription_id == VersionedString.id
    ).filter(Phrase.transcription == 'acimosisak').all()
    assert len(results) == 1


@pytest.fixture()
def acimosis(db):
    """
    Inserts the word 'acimosis'/'puppy' into the database.

    Returns the phrase.id of the inserted phrase.
    """
    word = Word(transcription='acîmosis', translation=' puppy  ')
    recording = Recording.new(phrase=word, input_file=TEST_WAV, speaker='NIL')
    # Insert it for the first time.
    db.session.add(recording)
    db.session.commit()
    return word.id


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
