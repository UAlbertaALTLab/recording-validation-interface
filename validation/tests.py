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

from validation.models import RecordingSession
from librecval.recording_session import TimeOfDay, Location, SessionID


@pytest.mark.django_db
def test_recording_session():
    session = mommy.make(RecordingSession)
    # Check all the fields.
    assert isinstance(session.date, datetype)
    assert session.time_of_day in {m.value for m in TimeOfDay} | {''}
    assert session.location in {m.value for m in Location} | {''}
    assert isinstance(session.subsession, (int, type(None)))


def test_recording_session_model_from_session_id():
    session_id = SessionID.from_name('2017-11-01-AM-OFF-_')
    session = RecordingSession.create_from(session_id)
    assert session.date == session_id.date
    assert session.time_of_day == session_id.time_of_day.name
    assert session.location == session_id.location.name
    assert session.subsession == session_id.subsession

    session.clean_fields()
    session.clean()

# TODO: create a recording session from a libreval recording session
