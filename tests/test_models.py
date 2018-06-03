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

from datetime import date
from pathlib import Path

import pytest  # type: ignore
from sqlalchemy.exc import SQLAlchemyError  # type: ignore

from recval.app import user_datastore
from recval.model import (ElicitationOrigin, Phrase, Recording,
                          RecordingSession, RecordingQuality, VersionedString,
                          Word)
from recval.recording_session import SessionID, TimeOfDay


def test_insert_word(db, wave_file_path, recording_session):
    """
    Insert a word, and retrieve it again.
    """

    word = Word(transcription=' acimosis', translation='puppy ')
    recording = Recording.new(fingerprint='acimosis', phrase=word,
                              input_file=wave_file_path, speaker='NIL',
                              session=recording_session)
    db.session.add(recording)
    db.session.commit()

    result_set = Word.query_by(translation='puppy').all()
    assert len(result_set) >= 1
    assert word in result_set

    result_set = Word.query_by(transcription='acimosis').all()
    assert len(result_set) >= 1
    assert word in result_set


def test_insert_recording_twice(db, wave_file_path, recording_session):
    """
    Insert the exact SAME recording twice; the second should fail.
    """

    word = Word(transcription='acimosis', translation='puppy')

    # Insert it once.
    rec1 = Recording.new(fingerprint='acimosis', phrase=word,
                         input_file=wave_file_path, speaker='NIL',
                         session=recording_session)
    db.session.add(rec1)
    db.session.commit()

    # Insert it again.
    rec2 = Recording.new(fingerprint='acimosis', phrase=word,
                         input_file=wave_file_path, speaker='NIL',
                         session=recording_session)
    db.session.add(rec1)
    with pytest.raises(SQLAlchemyError):
        db.session.commit()


def test_recording_date_automatically_set(db, recording_session):
    """
    Should set the recording's date automatically from the session.
    """
    word = Word(transcription='acimosis', translation='puppy')
    rec = Recording.new(fingerprint='acimosis', phrase=word,
                        session=recording_session)
    db.session.add(rec)
    db.session.commit()

    assert rec.timestamp.date() == recording_session.date


def test_transcription_update(db, wave_file_path, recording_session):
    """
    Ensure that a word's transcription can be changed.
    """

    word = Word(transcription='\n aci\u0302mosis \r', translation='puppy')
    recording = Recording.new(fingerprint='acimosis', phrase=word,
                              input_file=wave_file_path, speaker='NIL',
                              session=recording_session)
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
    rec_id = recording.id
    assert recording.quality is None

    # Update it...
    recording.quality = RecordingQuality.clean
    db.session.commit()
    del word
    del recording

    # And make sure it has changed.
    recording = Recording.query.filter_by(id=rec_id).one()
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

    results = Phrase.query_by(transcription=' acimosisak ').all()
    assert len(results) == 1


def test_authentication(db):
    from recval.model import User, user_datastore
    before = User.query.count()
    user_datastore.create_user(email='test@example.com',
                               password='<none>')
    db.session.commit()

    assert User.query.count() == before + 1


def test_search_full_translation(db, acimosis, acimosisak):
    """
    Test the full-text search feature for exact words in the translation.
    """
    word = Word.search_by('puppy').one()
    assert word.translation == 'puppy'


def test_search_full_transcription(db, acimosis, acimosisak):
    """
    Test the full-text search feature for exact words in the transcription.
    """
    word = Word.search_by('acimosisak').one()
    assert word.transcription == 'acimosisak'


def test_search_phrases(db, acimosis, acimosisak):
    """
    Test that you can search on both phrases and sentences.
    """
    p = Phrase.search_by('acimosisak').one()
    assert 'pup' in p.translation


def test_search_transcription_accents(db, acimosis, acimosisak):
    """
    Test the full-text search for matches with variations in transcription.
    """
    word = Word.search_by("ÂCIMOS'S").one()
    assert word.translation == 'puppy'


def test_versioned_string_author(db, validator):
    """
    Ensure that we can set an author for the given versioned string.
    """
    v = VersionedString.new('acimosis', author=validator)
    db.session.add(v)
    db.session.commit()
    del v

    v = VersionedString.query.filter_by(author=validator).one()
    assert v.author == validator


def test_derived_versioned_string(db, validator):
    """
    Ensure that we can derive a versioned string and have a different author.
    """
    from recval.database.special_users import importer

    v = VersionedString.new('acimos(is)', author=importer)
    original_id = v.id
    db.session.add(v)
    db.session.commit()
    del v

    original = VersionedString.query.filter_by(value='acimos(is)').one()
    derived = original.derive(value='acimosis', author=validator)
    db.session.add(derived)
    db.session.commit()
    del derived

    derived = VersionedString.query.filter_by(value='acimosis').one()
    assert original != derived
    assert original.provenance == original
    assert original.previous is None
    assert derived.previous == original
    assert derived.provenance == original
    assert original.author == importer
    assert derived.author == validator
    assert original.author != derived.author


def test_recording_has_session(db):
    """
    Ensures that a recording belongs to a session.
    """
    session_id = SessionID(date=date(2015, 12, 4),
                           time_of_day=TimeOfDay.MORNING,
                           location=None,
                           subsession=None)
    session = RecordingSession.from_session_id(session_id)

    assert session.id == session_id
    assert session.date == session_id.date
    assert session.time_of_day == session_id.time_of_day
    assert session.location == session_id.location

    db.session.add(session)
    db.session.commit()


@pytest.fixture
def acimosisak(db):
    word = Word(transcription='acimosisak', translation='litter of pups')
    db.session.add(word)
    db.session.commit()
