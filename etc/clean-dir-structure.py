#!/usr/bin/env python3.6

# 2018 © Eddie Antonio Santos. All rights reserved.

"""
Cleans up the directory structure for recording sessions.

>>> Session.from_name('sagiesbr-annotations2') is None
True
>>> s = Session.from_name('2018-01-24am2-kch')
>>> isinstance(s, Session)
True
>>> s.year
2018
>>> s.month
1
>>> s.day
24
>>> s.time_of_day == TimeOfDay.MORNING
True
>>> s.subsession
2
>>> s.location == Location.KITCHEN
True
>>> s.as_filename()
'2018-01-24-AM-KCH-2'

>>> s = Session.from_name('2016-11-7PMDS')
>>> s.time_of_day == TimeOfDay.AFTERNOON
True
>>> s.location == Location.DOWNSTAIRS
True
>>> s.as_filename()
'2016-11-07-PM-DS-0'

>>> s = Session.from_name('2016-01-18am')
>>> s.location is None
True
>>> s.as_filename()
'2016-01-18-AM-___-0'
"""

import re
from typing import NamedTuple, Optional
from pathlib import Path
from enum import Enum, auto
from datetime import date as datetype
from datetime import datetime


directory_pattern = re.compile(r'''
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
        raise ValueError(f'Unknown time of day: {code!r}')


class Location(Enum):
    KITCHEN = 'KCH'
    OFFICE = 'OFF'
    DOWNSTAIRS = 'DS'
    UPSTAIRS = 'US'

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
        raise ValueError(f'Unknown location code: {code!r})')


class Session(NamedTuple):
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
    def from_name(cls, directory_name: str) -> 'Session':
        m = directory_pattern.match(directory_name)
        if m is None:
            return None
        
        # Parse out all the things into appropriate datatypes.
        date = datetime.strptime(m.group('isodate'), '%Y-%m-%d').date()
        time_of_day = (m.group('time_of_day') and
                       TimeOfDay.parse(m.group('time_of_day')))
        subsession = m.group('subsession') and int(m.group('subsession'))
        location = m.group('location') and Location.parse(m.group('location'))

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
        


def resolve_bad_name(filename: str) -> Optional[Session]:
    return {
        '2017-04-20om-ds': Session(date=datetype(2017, 4, 20),
                                   subsession=None,
                                   time_of_day=TimeOfDay.AFTERNOON,
                                   location=Location.DOWNSTAIRS),
    }.get(filename, None)


def resolve_exception(filename: str) -> Optional[Session]:
    return {
        '2014-04-25-Maskwacis': None,
        '2017-02-16USAM': None,
    }.get(filename, None)


def find_session_dirs():
    """
    Return a list of pairs of (Path, Session).
    """
    sessions = []
    for entry in Path('.').iterdir():
        if not entry.is_dir():
            continue

        try:
            sesh = (
                Session.from_name(entry.stem) or
                resolve_bad_name(entry.stem)
            )
        except ValueError:
            log('Exceptional session name:', entry.stem)
            sesh = resolve_exception(entry.stem)

        if not sesh:
            log('Not a valid session:', entry.stem)
            continue

        sessions.append((entry, sesh))
    return sessions
        

def main():
    sessions = find_session_dirs()

    out_dir = Path('.') / 'sessions'
    out_dir.mkdir(exist_ok=True)
    for original_path, session in sessions:
        entry = out_dir / session.as_filename()
        try:
            entry.symlink_to(original_path.resolve(), target_is_directory=True)
        except FileExistsError:
            log("Will not overwrite duplicate session:", original_path)
            continue


def log(*args, **kwargs):
    from sys import argv
    from sys import stderr
    print(f"{argv[0]}:", *args, **kwargs, file=stderr)


if __name__ == '__main__':
    main()

# vim: set ts=4 sw=4 sts=4 et:
