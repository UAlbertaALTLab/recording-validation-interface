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

import pytest  # type: ignore

from librecval.recording_session import (
    Location,
    SessionID,
    SessionParseError,
    TimeOfDay,
)


def test_does_not_parse_arbitrary_directory_name():
    with pytest.raises(SessionParseError):
        SessionID.from_name("sagiesbr-annotations2")


def test_basic_parsing():
    s = SessionID.from_name("2018-01-24-AM-KCH-2")
    assert isinstance(s, SessionID)
    assert s.year == 2018
    assert s.month == 1
    assert s.day == 24
    assert s.time_of_day == TimeOfDay.MORNING
    assert s.subsession == 2
    assert s.location == Location.KITCHEN
    assert s.as_filename() == "2018-01-24-AM-KCH-2"


def test_trickier_parse():
    s = SessionID.from_name("2016-11-07-PM-DS-0")
    assert s.time_of_day == TimeOfDay.AFTERNOON
    assert s.location == Location.DOWNSTAIRS
    assert s.as_filename() == "2016-11-07-PM-DS-0"


def test_location_missing():
    s = SessionID.from_name("2016-01-18-AM-___-0")
    assert s.time_of_day == TimeOfDay.MORNING
    assert s.location is None
    assert s.as_filename() == "2016-01-18-AM-___-0"


def test_time_of_day_missing():
    s = SessionID.from_name("2016-01-18-__-OFF-0")
    assert s.time_of_day is None
    assert s.location is Location.OFFICE
    assert s.as_filename() == "2016-01-18-__-OFF-0"


def test_str_is_same_as_filename():
    s = SessionID.from_name("2016-01-18-AM-OFF-0")
    assert str(s) == s.as_filename()


def test_unspecified_subsession():
    s = SessionID.from_name("2016-01-18-AM-OFF-_")
    assert s.subsession is None
    assert str(s) == s.as_filename()


def test_parse_dirty():
    actual = SessionID.parse_dirty("2015-04-15-am")
    expected = SessionID(
        date=date(2015, 4, 15),
        subsession=None,
        time_of_day=TimeOfDay.MORNING,
        location=None,
    )
    assert actual == expected
