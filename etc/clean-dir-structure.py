#!/usr/bin/env python3.6

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

"""
Cleans up the directory structure for recording sessions.

Dumps the cleaned up names in ./samples/

This script works by iterating through ALL of the diretories in the current
working directory, minus the ones in the IGNORE list (see below) and tries to
parse the name of each directory as a session name. The session names are
roughly in a parseable manner, but they are not especially consistent over
time. As a result, there is an EXCEPTION list that is checked before to return
an explicit session.

The sessions are collected, and symbolic links are created to the true
directories.

**This script makes no attempt to rename or overwrite existing data!***

---

Unit tests:

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
from datetime import date as datetype
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import AnyStr, Callable, Match, NamedTuple, Optional, TypeVar

# Pattern that tries to match and parse most folder names.
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
    def from_name(cls, directory_name: str) -> Optional['Session']:
        m = directory_pattern.match(directory_name)
        if m is None:
            return None

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


def main():
    """
    Finds all directories that look like sessions, and reorganizes them into
    sessions/.
    """
    cwd = Path('.')
    assert cwd.resolve() == Path('/data/av/backup-mwe'), (
        "I'm expecting this script to run in backup-mwe, "
        f"but I'm actually in {cwd}"
    )

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


# Files to explicilty ignore.
IGNORE = (
    '2014-04-25-Maskwacis',  # XXX: add to exceptions?
    '2014-06-16-Maskwacis',  # XXX: add to exceptions?
    '2014-12-09-Maskwacis',  # XXX: add to exceptions?
    '2015-02-09_English_snow',  # XXX: add to exceptions?
    '2015-03-18-Maskwacis',  # XXX: add to exceptions?
    '2016-11-18_est',  # XXX: add to exceptions?
    '2016-11-amDS',  # XXX: add to exceptions
    '2017-05-04amUSPM',  # XXX: add to exceptions?
    '2017-07-15ETHNOBOTANY',  # XXX: add to exceptions?
    '2017-11-08am-OFF',  # Uppercase duplicate of 2017-11-08am-OFF
    '2017-11-08pm-OFF',  # Uppercase duplicate of 2017-11-08am-OFF
    '2017-10-25am-KCH',  # Duplicate of 2017-10-25am-kit
    '2017-10-25-pm-KCH',  # Duplicate of 2017-10-25i-pm-kit
    '2015-09-21am1_data',
    '2015-09-21am2_data',
    'AdvancedCreeRecordings',
    'ahtest',
    'ANNOTATION2015-05-05am',
    'badmeg_annotations',
    'mjerry-annotations',
    'mjtest',
    'My Passport for Mac 1',
    'PsalmRaw',
    '__pycache__',
    'sagiesbr-annotations',
    'sagiesbr-annotations2',
    'sessions',
    'test',
    'test123',
    'test2',
    'tim-clean',
    'treule_annotations',
)

# Files that require special handling.
EXCEPTIONS = {
    '2016-02-16USPM':   Session.from_name('2016-02-16PM-US'),
    '2016-10-24pmB-US': Session.from_name('2016-10-24PM2-US'),
    '2016-10-24pmC-US': Session.from_name('2016-10-24PM3-US'),
    '2016-10-31pmDS2':  Session.from_name('2016-10-31PM2-DS'),
    '2016-11-28am-US2': Session.from_name('2016-11-28AM2-US'),
    '2016-11-28am-US3': Session.from_name('2016-11-28AM3-US'),
    '2016-11-28pm-US2': Session.from_name('2016-11-28PM2-US'),
    '2017-01-19-DS-am': Session.from_name('2017-01-19AM-DS'),
    '2017-01-19-DS-pm': Session.from_name('2017-01-19PM-DS'),
    '2017-02-02USAM':   Session.from_name('2017-02-02AM-US'),
    '2017-02-02USPM':   Session.from_name('2017-02-02PM-US'),
    '2017-02-16USAM':   Session.from_name('2017-02-16AM-US'),
    '2017-02-16USAM':   Session.from_name('2017-02-16AM-US'),
    '2017-03-09USam':   Session.from_name('2017-03-09AM-US'),
    '2017-03-09USpm':   Session.from_name('2017-03-09PM-US'),
    '2017-04-20om-ds':  Session.from_name('2017-04-20PM-DS'),
}


def find_session_dirs():
    """
    Return a list of pairs of (Path, Session).
    """
    sessions = []
    for entry in Path('.').iterdir():
        filename = entry.stem
        if not entry.is_dir():
            continue

        if filename in IGNORE:
            continue
        elif filename in EXCEPTIONS:
            sesh = EXCEPTIONS[filename]
        else:
            try:
                sesh = Session.from_name(filename)
            except ValueError:
                log(f"invalid name:", repr(filename))
                raise

        if not sesh:
            raise ValueError(f'Not a valid session: {filename!r}')

        sessions.append((entry, sesh))
    return sessions


def log(*args, **kwargs):
    from sys import argv
    from sys import stderr
    print(f"{argv[0]}:", *args, **kwargs, file=stderr)


if __name__ == '__main__':
    main()
# vim: set ts=4 sw=4 sts=4 et:
