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

from recval.model import (ElicitationOrigin, Phrase, Recording,
                          RecordingSession, RecordingQuality,
                          Word)
from recval.recording_session import SessionID, TimeOfDay


@pytest.mark.skip
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


@pytest.mark.skip
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


@pytest.mark.skip
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
