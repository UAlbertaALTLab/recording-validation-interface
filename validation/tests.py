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

from datetime import date as datetype

import pytest
from django.core.exceptions import ValidationError
from hypothesis import given
from hypothesis.strategies import builds
from model_mommy import mommy
from model_mommy.recipe import Recipe

from librecval.normalization import nfc
from librecval.recording_session import Location, SessionID, TimeOfDay
from validation.models import Phrase, RecordingSession, Speaker


def test_recording_session():
    session = mommy.prepare(RecordingSession)
    # Check all the fields.
    assert isinstance(session.date, datetype)
    assert session.time_of_day in {m.value for m in TimeOfDay} | {''}
    assert session.location in {m.value for m in Location} | {''}
    assert isinstance(session.subsession, (int, type(None)))


@given(builds(SessionID))
def test_recording_session_model_from_session_id(session_id):
    """
    Test that a RecordingSession model can be make from a SessionID, and that
    it can be converted back.
    """

    # Create the RecordingSession from the session ID.
    session = RecordingSession.create_from(session_id)
    assert session.date == session_id.date
    assert session.time_of_day == (session_id.time_of_day and session_id.time_of_day.value)
    assert session.location == (session_id.location and session_id.location.value)
    assert session.subsession == session_id.subsession

    # Make sure it passes validation!
    session.clean_fields()
    session.clean()

    # Now convert it back. We should get back an equivillent object.
    new_session_id = session.as_session_id()
    assert new_session_id == session_id

    # Finally, the str() should be based on the str() of the SessionID:
    assert str(session_id) in str(session)


def test_speaker():
    """
    Check that we can create a speaker.
    """
    speaker = mommy.prepare(Speaker)
    speaker.clean()
    assert speaker.code.upper() == speaker.code
    assert isinstance(speaker.full_name, str)
    assert speaker.gender in ('M', 'F', None)


def test_speaker_validation():
    """
    Check that we can create a speaker.
    """
    speaker = Recipe(Speaker, code=' 43!341k43j1k ').prepare()

    with pytest.raises(ValidationError):
        speaker.clean()


def test_phrase():
    """
    Test that we can create a phrase instance.
    """
    phrase = mommy.prepare(Phrase)
    assert isinstance(phrase.transcription, str)
    assert isinstance(phrase.translation, str)
    assert phrase.kind in (Phrase.WORD, Phrase.SENTENCE)
    assert isinstance(phrase.validated, bool)
    assert phrase.transcription in str(phrase)
    assert phrase.origin in (None, Phrase.MASKWACÎS_DICTIONARY, Phrase.NEW_WORD)


@pytest.mark.parametrize('dirty_transcription', [
    'ni\N{COMBINING CIRCUMFLEX ACCENT}piy',
    '  n\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}piy ',
    '  ni\N{COMBINING CIRCUMFLEX ACCENT}piy ',
    ' Maskwacîs ',
    'n\N{LATIN SMALL LETTER I WITH MACRON}piy',
])
def test_phrase_transcription_normalization(dirty_transcription):
    """
    Test that the transcription gets normalized as a Cree phrase.
    """
    phrase = Recipe(Phrase, transcription=dirty_transcription).prepare()
    phrase.clean()
    assert phrase.transcription == nfc(phrase.transcription)
    # Should not have any leading spaces
    assert not phrase.transcription.startswith(' ')
    # Should not have any trailing spaces
    assert not phrase.transcription.endswith(' ')
    # SRO is ALWAYS lowercase!
    assert phrase.transcription.lower() == phrase.transcription

    vowels_with_macrons = {
        '\N{LATIN SMALL LETTER E WITH MACRON}',
        '\N{LATIN SMALL LETTER I WITH MACRON}',
        '\N{LATIN SMALL LETTER O WITH MACRON}',
        '\N{LATIN SMALL LETTER A WITH MACRON}',
    }

    assert vowels_with_macrons.isdisjoint(phrase.transcription)
