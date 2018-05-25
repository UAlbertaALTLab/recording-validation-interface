#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © Eddie Antonio Santos. All rights reserved.

import re
from datetime import date as datetype
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import AnyStr, Callable, Match, NamedTuple, Optional, TypeVar

# This a strict pattern, that differs from the one in etc/;
# It matches only directories with the normalized naming conventions.
strict_pattern = re.compile(r'''
    \A
    (?P<isodate>
        \d{4}-\d{1,2}-\d{1,2}   (?# This is slightly inaccurate, but it's okay. )
    )
    -
    (?:
        (?P<time_of_day> AM|PM) | __
    )
    -
    (?:
        (?P<location> US|DS|KCH|OFF) |  ___
    )
    -
    (?P<subsession>
        \d+
    )
    \Z
''', re.VERBOSE)


# Pattern that tries to match and parse most folder names.
dirty_pattern = re.compile(r'''
    \A
    (?P<isodate>
        \d{4}-\d{1,2}-\d{1,2}
    )
    (                           (?# More specific information about the session )
        (
            (-|_)?
            (?P<time_of_day>
                [AaPp][Mm]
            )
            (?P<subsession>
                \d+             (?# Some sessions are split further than just AM/PM )
            )?
        )?
        (
            (-|_)?
            (?P<location>
                \w+
            )
        )?
    )
    \Z
''', re.VERBOSE)



# ############################### Exceptions ############################# #


class SessionParseError(ValueError):
    """
    Thrown when a session cannot be parsed.
    """


class InvalidTimeOfDayError(SessionParseError):
    def __init__(self, code: str) -> None:
        super().__init__(f"Unknown time of day: {code!r}")


class InvalidLocationError(SessionParseError):
    def __init__(self, code: str) -> None:
        super().__init__(f'Unknown location code: {code!r}')


# ############################## Enumerations ############################ #


class TimeOfDay(Enum):
    MORNING = 'AM'
    AFTERNOON = 'PM'

    @staticmethod
    def parse(text: str) -> 'TimeOfDay':
        code = text.upper()
        if code == 'AM':
            return TimeOfDay.MORNING
        elif code == 'PM':
            return TimeOfDay.AFTERNOON
        raise InvalidTimeOfDayError(text)


class Location(Enum):
    # For the first three years of recording:
    DOWNSTAIRS = 'DS'  # Downstairs in Sohki house
    UPSTAIRS = 'US'  # Upstairs in Sohki house
    # For the last academic year of recording:
    KITCHEN = 'KCH'  # Kitchen in Miyo head office
    OFFICE = 'OFF'  # Office in Miyo head office

    @staticmethod
    def parse(text: str) -> 'Location':
        code = text.upper()
        if code in ('KCH', 'KIT'):
            return Location.KITCHEN
        elif code == 'OFF':
            return Location.OFFICE
        elif code in ('DS', 'DOWNSTAIRS'):
            return Location.DOWNSTAIRS
        elif code in ('US', 'UPSTAIRS'):
            return Location.UPSTAIRS
        raise InvalidLocationError(text)


class SessionID(NamedTuple):
    date: datetype
    time_of_day: Optional[TimeOfDay]
    subsession: Optional[int]
    location: Optional[Location]

    @property
    def year(self):
        return self.date.year

    @property
    def month(self):
        return self.date.month

    @property
    def day(self):
        return self.date.day

    @classmethod
    def from_name(cls, directory_name: str) -> 'SessionID':
        m = strict_pattern.match(directory_name)
        if m is None:
            raise SessionParseError(f"directory does not match pattern {directory_name}")

        # Parse out all the things into appropriate datatypes.
        date = datetime.strptime(m.group('isodate'), '%Y-%m-%d').date()
        time_of_day = apply_or_none(TimeOfDay.parse, m.group('time_of_day'))
        subsession = apply_or_none(int, m.group('subsession'))
        location = apply_or_none(Location.parse, m.group('location'))

        return cls(date=date,
                   time_of_day=time_of_day,
                   subsession=subsession,
                   location=location)

    def as_filename(self) -> str:
        """
        Returns a standardized filename for any session.
        """
        time = (self.time_of_day and self.time_of_day.value) or '__'
        loc = (self.location and self.location.value) or '___'
        subsesh = self.subsession or 0
        return f"{self.date:%Y-%m-%d}-{time}-{loc}-{subsesh:1d}"

    def __str__(self) -> str:
        return self.as_filename()

    @classmethod
    def parse_dirty(cls, name: str) -> 'SessionID':
        """
        Attempts to parse a messy session name.

        >>> SessionID.parse_dirty('2015-04-15-am')
        SessionID(date=date(2015, 4, 15), time_of_day=TimeOfDay.MORNING, subsession=None, location=None)
        """
        m = dirty_pattern.match(name)
        if m is None:
            raise SessionParseError(f"session could not be parsed: {name!r}")

        # Parse out all the things into appropriate datatypes.
        date = datetime.strptime(m.group('isodate'), '%Y-%m-%d').date()
        time_of_day = apply_or_none(TimeOfDay.parse, m.group('time_of_day'))
        subsession = apply_or_none(int, m.group('subsession'))
        location = apply_or_none(Location.parse, m.group('location'))

        return cls(date=date,
                   time_of_day=time_of_day,
                   subsession=subsession,
                   location=location)

T = TypeVar('T')


def apply_or_none(fn: Callable[[AnyStr], T],
                  match: Optional[AnyStr]) -> Optional[T]:
    """
    Applies fn to the match ONLY if the match is not None.

    This is similar to >>= from Haskell.
    """
    if match is not None:
        return fn(match)
    return None
