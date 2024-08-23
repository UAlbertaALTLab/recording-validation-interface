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

import random
from datetime import date as datetype
from datetime import datetime

import pytest  # type: ignore
from django.core.exceptions import ValidationError  # type: ignore
from hypothesis import assume, given
from model_bakery import baker  # type: ignore
from model_bakery.recipe import Recipe  # type: ignore

from librecval.normalization import nfc
from librecval.recording_session import Location, SessionID, TimeOfDay
from librecval.test_utils.strategies import session_ids
from validation.models import Phrase, Recording, RecordingSession, Speaker


def test_recording_session():
    session = baker.prepare(RecordingSession)
    # Check all the fields.
    assert isinstance(session.date, datetype)
    assert session.time_of_day in {m.value for m in TimeOfDay} | {""}
    assert session.location in {m.value for m in Location} | {""}
    assert isinstance(session.subsession, (int, type(None)))


@given(session_ids())
def test_recording_session_model_from_session_id(session_id):
    """
    Test that a RecordingSession model can be make from a SessionID, and that
    it can be converted back.
    """

    # Create the RecordingSession from the session ID.
    session = RecordingSession.create_from(session_id)
    assert session.date == session_id.date
    if session_id.time_of_day is None:
        assert session.time_of_day == ""
    else:
        assert session.time_of_day == session_id.time_of_day.value
    if session_id.location is None:
        assert session.location == ""
    else:
        assert session.location == session_id.location.value
    assert session.subsession == session_id.subsession

    # Make sure it passes validation!
    session.clean_fields()
    session.clean()

    # Now convert it back. We should get back an equivalent object.
    new_session_id = session.as_session_id()
    assert new_session_id == session_id

    # Finally, the str() should be based on the str() of the SessionID:
    assert str(session_id) in str(session)


@pytest.mark.django_db(transaction=True)
@given(session_ids())
def test_inserting_duplicate_session(session_id: SessionID):
    """
    Check that we can't insert the same session in the database.
    """

    original = RecordingSession.create_from(session_id)
    duplicate = RecordingSession.create_from(session_id)
    # This tests assumes that the duplicate is equivalent, but is not the SAME object!
    assert original.as_session_id() == duplicate.as_session_id()
    assert original is not duplicate

    original.save()
    with pytest.raises(ValidationError):
        # This is required on SQLite3, which will not check this for you (???)
        duplicate.validate_unique()
        duplicate.save()


@pytest.mark.django_db(transaction=True)
@given(session_ids())
def test_fetching_by_session_id(session_id: SessionID):
    """
    Check that we can create a RecordingSession, then fetch it by session ID.
    """
    original = RecordingSession.create_from(session_id)
    original.save()
    del original

    query = RecordingSession.objects_by_id(session_id)
    assert len(query) == 1
    fetched = query.first()
    assert fetched.as_session_id() == session_id


@pytest.mark.django_db(transaction=True)
@given(session_ids())
def test_get_or_create_recording_session(session_id: SessionID):
    """
    Test get or creating a recording session.
    """

    # Skip any session already inserted.
    assume(len(RecordingSession.objects_by_id(session_id)) == 0)

    # Try fetching for the first time; it should be created.
    original, created = RecordingSession.get_or_create_by_session_id(session_id)
    assert created is True
    assert original.as_session_id() == session_id
    del original

    # Try fetching it again; it should fetch the old version.
    fetched, created = RecordingSession.get_or_create_by_session_id(session_id)
    assert created is False
    assert fetched.as_session_id() == session_id


def test_speaker():
    """
    Check that we can create a speaker.
    """
    speaker = baker.prepare(Speaker)
    speaker.clean()
    assert speaker.code.upper() == speaker.code
    assert isinstance(speaker.full_name, str)
    assert speaker.gender in ("M", "F", None)
    assert speaker.code in str(speaker)


def test_speaker_validation():
    """
    Check that we can create a speaker.
    """
    speaker = Recipe(Speaker, code=" 43!341k43j1k ").prepare()

    with pytest.raises(ValidationError):
        speaker.clean()


def test_phrase():
    """
    Test that we can create a phrase instance.
    """
    phrase = baker.prepare(Phrase)
    assert isinstance(phrase.transcription, str)
    assert isinstance(phrase.translation, str)
    assert phrase.kind in (Phrase.WORD, Phrase.SENTENCE)
    assert isinstance(phrase.validated, bool)
    assert phrase.transcription in str(phrase)
    assert phrase.origin in (None, Phrase.MASKWACÎS_DICTIONARY, Phrase.NEW_WORD)


@pytest.mark.parametrize(
    "dirty_transcription",
    [
        "ni\N{COMBINING CIRCUMFLEX ACCENT}piy",
        "  n\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}piy ",
        "  ni\N{COMBINING CIRCUMFLEX ACCENT}piy ",
        " Maskwacîs ",
        "n\N{LATIN SMALL LETTER I WITH MACRON}piy",
        "n\N{LATIN CAPITAL LETTER I WITH MACRON}piy",
        "Amiskwaciy - wâskahikanihk",
    ],
)
def test_phrase_transcription_normalization(dirty_transcription):
    """
    Test that the transcription gets normalized as a Cree phrase.
    """
    phrase = Recipe(
        Phrase,
        transcription=dirty_transcription,
        field_transcription=dirty_transcription,
        kind=Phrase.WORD,
    ).prepare()
    phrase.clean()
    assert phrase.transcription == nfc(phrase.transcription)
    # Should not have any leading spaces
    assert not phrase.transcription.startswith(" ")
    # Should not have any trailing spaces
    assert not phrase.transcription.endswith(" ")
    # SRO is ALWAYS lowercase!
    assert phrase.transcription.lower() == phrase.transcription

    vowels_with_macrons = {
        "\N{LATIN SMALL LETTER E WITH MACRON}",
        "\N{LATIN SMALL LETTER I WITH MACRON}",
        "\N{LATIN SMALL LETTER O WITH MACRON}",
        "\N{LATIN SMALL LETTER A WITH MACRON}",
    }

    # Ensure macrons are nowhere to be found in the transcription.
    assert vowels_with_macrons.isdisjoint(phrase.transcription)


@pytest.mark.parametrize(
    "dirty_transcription, expected",
    [
        ("Amiskwaciy-wâskahikanihk", "amiskwaciy-wâskahikanihk"),
        (" namôya \n\tninisitohtên  ", "namôya ninisitohtên"),
    ],
)
def test_phrase_transcription_normalization_hyphenation(dirty_transcription, expected):
    """
    Test that words in the transcriptions are separated by exactly one space,
    and have exactly one hyphen between morphemes.
    """
    phrase = Recipe(
        Phrase,
        transcription=dirty_transcription,
        field_transcription=dirty_transcription,
        kind=Phrase.WORD,
    ).prepare()
    phrase.clean()
    assert phrase.transcription == expected


def test_phrase_transcription_normalize_ê():
    """
    Tests that e gets converted to ê.
    """
    phrase = Recipe(
        Phrase,
        transcription="e-cacâstapiwet",
        field_transcription="e-cacâstapiwet",
        kind=Phrase.WORD,
    ).prepare()
    phrase.clean()
    assert phrase.transcription == "ê-cacâstapiwêt"


@pytest.mark.django_db
def test_phrase_has_history():
    """
    Test that we can insert an entry in the database, and that it has history.
    """
    changed = "ê-cacâstapiwêt"

    # Store a phrase in the database and forget about it.
    original = "ecastapiwet"
    phrase = Recipe(
        Phrase, transcription=original, field_transcription=original
    ).prepare()
    # Do NOT call clean, in order to simulate an initial import.
    phrase.save()
    phrase_id = phrase.id
    del phrase

    # Fetch it and change it, to create a new historical version of it.
    # and fuggettaboutit.
    phrase = Phrase.objects.get(id=phrase_id)
    phrase.transcription = changed
    phrase.field_transcription = changed
    phrase.clean()
    phrase.save()
    del phrase

    # Time has passed, let's make sure all the historical changes are there:
    phrase = Phrase.objects.get(id=phrase_id)
    assert phrase.transcription != original
    assert phrase.transcription == changed

    # Now, let's check the history!
    assert len(phrase.history.all()) == 2
    assert phrase.history.earliest().transcription == original


@pytest.mark.django_db
def test_recording():
    # Keep it in a 32 bit signed integer
    MAX_RECORDING_LENGTH = 2**31 - 1

    recording = Recipe(
        Recording, timestamp=lambda: random.randint(0, MAX_RECORDING_LENGTH)
    ).make()

    # Check all the fields.
    assert isinstance(recording.id, str)
    assert recording.quality in {Recording.GOOD, Recording.BAD, ""}
    assert isinstance(recording.timestamp, int)
    assert 0 <= recording.timestamp < MAX_RECORDING_LENGTH
    assert isinstance(recording.phrase, Phrase)
    if recording.session:
        assert isinstance(recording.session, RecordingSession)
    assert isinstance(recording.speaker, Speaker)

    assert hasattr(recording, "history")

    # Check its __str__() method.
    assert str(recording.phrase) in str(recording)
    assert str(recording.speaker) in str(recording)
    assert str(recording.session) in str(recording)


@pytest.mark.django_db
def test_phrase_recordings():
    # Keep it in a 32 bit signed integer
    MAX_RECORDING_LENGTH = 2**31 - 1

    phrase = baker.make(Phrase)

    r1 = Recipe(
        Recording,
        phrase=phrase,
        timestamp=lambda: random.randint(0, MAX_RECORDING_LENGTH),
    ).make()
    r2 = Recipe(
        Recording,
        phrase=phrase,
        timestamp=lambda: random.randint(0, MAX_RECORDING_LENGTH),
    ).make()

    assert len(phrase.recordings) == 2
    assert r1 in phrase.recordings
    assert r2 in phrase.recordings
