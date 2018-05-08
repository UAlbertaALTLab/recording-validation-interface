#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © Eddie Antonio Santos. All rights reserved.

import pytest  # type: ignore
from recval.recording_session import RecordingSession, TimeOfDay, Location
from recval.recording_session import SessionParseError


def test_does_not_parse_arbitrary_directory_name():
    with pytest.raises(SessionParseError):
        RecordingSession.from_name('sagiesbr-annotations2')


def test_basic_parsing():
    s = RecordingSession.from_name('2018-01-24-AM-KCH-2')
    assert isinstance(s, RecordingSession)
    assert s.year == 2018
    assert s.month == 1
    assert s.day == 24
    assert s.time_of_day == TimeOfDay.MORNING
    assert s.subsession == 2
    assert s.location == Location.KITCHEN
    assert s.as_filename() == '2018-01-24-AM-KCH-2'


def test_trickier_parse():
    s = RecordingSession.from_name('2016-11-07-PM-DS-0')
    assert s.time_of_day == TimeOfDay.AFTERNOON
    assert s.location == Location.DOWNSTAIRS
    assert s.as_filename() == '2016-11-07-PM-DS-0'


def test_location_missing():
    s = RecordingSession.from_name('2016-01-18-AM-___-0')
    assert s.time_of_day == TimeOfDay.MORNING
    assert s.location is None
    assert s.as_filename() == '2016-01-18-AM-___-0'


def test_time_of_day_missing():
    s = RecordingSession.from_name('2016-01-18-__-OFF-0')
    assert s.time_of_day is None
    assert s.location is Location.OFFICE
    assert s.as_filename() == '2016-01-18-__-OFF-0'


def test_str_is_same_as_filename():
    s = RecordingSession.from_name('2016-01-18-AM-OFF-0')
    assert str(s) == s.as_filename()
