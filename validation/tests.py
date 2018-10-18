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
from model_mommy import mommy
from hypothesis import given
from hypothesis.strategies import builds

from validation.models import RecordingSession, Speaker
from librecval.recording_session import TimeOfDay, Location, SessionID


@pytest.mark.django_db
def test_recording_session():
    session = mommy.make(RecordingSession)
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


@pytest.mark.django_db
def test_speaker():
    """
    Check that we can create a speaker.
    """
    speaker = mommy.make(Speaker)
    speaker.clean()
    assert speaker.code.upper() == speaker.code
    assert isinstance(speaker.full_name, str)
