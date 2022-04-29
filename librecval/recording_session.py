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

import csv
import re
from datetime import date as datetype
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    AnyStr,
    Callable,
    Dict,
    List,
    Match,
    NamedTuple,
    Optional,
    TextIO,
    TypeVar,
)

import logme  # type: ignore


T = TypeVar("T")

# This a strict pattern, that differs from the one in etc/;
# It matches only directories with the normalized naming conventions.
strict_pattern = re.compile(
    r"""
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
    (?:
        (?P<subsession> \d+) | _
    )
    \Z
""",
    re.VERBOSE,
)


# Pattern that tries to match and parse most folder names.
dirty_pattern = re.compile(
    r"""
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
""",
    re.VERBOSE,
)


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
        super().__init__(f"Unknown location code: {code!r}")


# ############################## Enumerations ############################ #


class TimeOfDay(Enum):
    MORNING = "AM"
    AFTERNOON = "PM"

    @staticmethod
    def parse(text: str) -> "TimeOfDay":
        code = text.upper()
        if code == "AM":
            return TimeOfDay.MORNING
        elif code == "PM":
            return TimeOfDay.AFTERNOON
        raise InvalidTimeOfDayError(text)


class Location(Enum):
    # For the first three years of recording:
    DOWNSTAIRS = "DS"  # Downstairs in Sohki house
    UPSTAIRS = "US"  # Upstairs in Sohki house
    # For the last academic year of recording:
    KITCHEN = "KCH"  # Kitchen in Miyo head office
    OFFICE = "OFF"  # Office in Miyo head office

    @staticmethod
    def parse(text: str) -> "Location":
        code = text.upper()
        if code in ("KCH", "KIT"):
            return Location.KITCHEN
        elif code == "OFF":
            return Location.OFFICE
        elif code in ("DS", "DOWNSTAIRS"):
            return Location.DOWNSTAIRS
        elif code in ("US", "UPSTAIRS"):
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
    def from_name(cls, directory_name: str) -> "SessionID":
        m = strict_pattern.match(directory_name)
        if m is None:
            raise SessionParseError(
                f"directory does not match pattern {directory_name}"
            )

        # Parse out all the things into appropriate datatypes.
        date = datetime.strptime(m.group("isodate"), "%Y-%m-%d").date()
        time_of_day = apply_or_none(TimeOfDay.parse, m.group("time_of_day"))
        subsession = apply_or_none(int, m.group("subsession"))
        location = apply_or_none(Location.parse, m.group("location"))

        return cls(
            date=date, time_of_day=time_of_day, subsession=subsession, location=location
        )

    def as_filename(self) -> str:
        """
        Returns a standardized filename for any session.
        """
        time = (self.time_of_day and self.time_of_day.value) or "__"
        loc = (self.location and self.location.value) or "___"
        subsesh = "_" if self.subsession is None else self.subsession
        return f"{self.date:%Y-%m-%d}-{time}-{loc}-{subsesh}"

    def __str__(self) -> str:
        return self.as_filename()

    @classmethod
    def parse_dirty(cls, name: str) -> "SessionID":
        """
        Attempts to parse a messy session name.
        >>> sid = SessionID.parse_dirty('2015-04-15-am')
        >>> sid.date
        datetime.date(2015, 4, 15)
        >>> sid.time_of_day == TimeOfDay.MORNING
        True
        >>> sid.subsession is None
        True
        >>> sid.location is None
        True
        """
        m = dirty_pattern.match(name)
        if m is None:
            raise SessionParseError(f"Session could not be parsed: {name!r}")

        # Parse out all the things into appropriate datatypes.
        date = datetime.strptime(m.group("isodate"), "%Y-%m-%d").date()
        time_of_day = apply_or_none(TimeOfDay.parse, m.group("time_of_day"))
        subsession = apply_or_none(int, m.group("subsession"))
        location = apply_or_none(Location.parse, m.group("location"))

        return cls(
            date=date, time_of_day=time_of_day, subsession=subsession, location=location
        )


class SessionMetadata:
    """
    Metadata for a single session, obtained from "Master Recordings MetaData"
    on Google Sheets.
    """

    def __init__(
        self, session: SessionID, raw_name: str, rapid_words, mics=Dict[int, str]
    ) -> None:
        self.session = session
        self.raw_name = raw_name
        self.mics = mics
        self.rapid_words = rapid_words

    def __getitem__(self, index: int) -> Optional[str]:
        """
        Return the ONE-INDEXED speaker's name.
        """
        if index == "rapid_words":
            return self.rapid_words
        if index not in self.mics.keys():
            raise IndexError(f"Invalid mic number: {index}")
        return self.mics.get(index, None)

    def __repr__(self) -> str:
        return (
            f"{type(self).__qualname__}("
            f"session={self.session!r}, "
            f"raw_name={self.raw_name!r}, "
            f"mics={self.mics!r}, "
            f"rapid_words={self.rapid_words!r}"
            ")"
        )

    @classmethod
    def parse(cls, row: Dict[str, Any], session_name: str = None) -> "SessionMetadata":
        """
        Parses a row from the metadata CSV file.
        Can pass an explicit session name to override what's written in the
        "SESSION" column.
        """
        # Extract "raw" name
        raw_name = row["SESSION"]

        # Parse a session out of it
        effective_name = session_name or raw_name
        try:
            session = SessionID.from_name(effective_name)
        except SessionParseError:
            session = SessionID.parse_dirty(effective_name)

        # Who are speaking on the mics?
        mic_names = [key for key in row.keys() if key.startswith("MIC")]
        assert len(mic_names) >= 3
        mics = {
            number_from(mic): normalize_speaker_name(row[mic])
            for mic in sorted(mic_names)
        }

        # TODO: parse the elicitation sheets
        rapid_words_section = row["Rapidwords Section(s)"].split(",")
        for i, section in enumerate(rapid_words_section):
            if "." not in section:
                try:
                    numerals = rapid_words_section[i - 1].replace("_", " ").split()[0]
                    section = numerals + section
                    rapid_words_section[i] = section
                except:
                    print("Could not parse section: ", section)

        return cls(
            session=session,
            raw_name=raw_name,
            rapid_words=rapid_words_section,
            mics=mics,
        )


class Overrides:
    """
    Any overridden properties when writing the
    """

    def __init__(self, raw_name: str, **options):
        self.raw_name = raw_name
        self._options = options

    @property
    def effective_name(self) -> str:
        try:
            return self._options["name"]
        except KeyError:
            return self.raw_name

    @property
    def should_skip(self) -> bool:
        return self._options.get("skip", False)

    @classmethod
    def parse(cls, raw_name: str, override_text: str) -> "Overrides":
        clean_name = raw_name.strip()
        override = override_text.strip()

        # Nothing to override, so just have the cleaned name.
        if not override:
            return Overrides(clean_name)

        # A rename starts with a well-formatted Session ID
        # An options starts with !
        rename, _, raw_options_text = override.partition("!")

        options = {}  # type: Dict[str, Any]

        # Add the rename to the options
        if rename.strip():
            options["name"] = rename.strip()

        # For now, options are just boolean flags
        for option in raw_options_text.split():
            options[option.lower()] = True

        return Overrides(clean_name, **options)


@logme.log
def parse_metadata(metadata_file: TextIO, logger) -> Dict[SessionID, SessionMetadata]:
    """
    Given an opened CSV file, returns a dictionary mapping a session
    identifier to its metadata (e.g., speaker codes, elicitation sheets,
    etc.).
    """
    reader = csv.DictReader(metadata_file)

    sessions: Dict[SessionID, SessionMetadata] = {}
    for row in reader:
        if not row["SESSION"]:
            continue
        raw_name = row["SESSION"]

        # Get any overridden settings.
        override = Overrides.parse(raw_name, row.get("RECVAL_OVERRIDE", ""))

        if override.should_skip:
            logger.info("Skipping %s (marked with !SKIP)", row["SESSION"])
            continue

        try:
            s = SessionMetadata.parse(row, session_name=override.effective_name)
        except SessionParseError:
            logger.exception("Could not parse: %s", row)
            # We'll just skip this row...
        else:
            if raw_name != override.effective_name:
                logger.info(
                    "Using renamed session: %r instead of %r",
                    override.effective_name,
                    raw_name,
                )
            sessions[s.session] = s
    return sessions


def apply_or_none(fn: Callable[[AnyStr], T], match: Optional[AnyStr]) -> Optional[T]:
    """
    Applies fn to the match ONLY if the match is not None.
    This is similar to >>= from Haskell.
    """
    if match is not None:
        return fn(match)
    return None


def number_from(mic_name: str) -> int:
    """
    Return the mic number.
    """
    assert mic_name.startswith("MIC")
    n = int(mic_name.split()[1])
    assert 1 <= n <= 10
    return n


def normalize_speaker_name(name: str) -> Optional[str]:
    """
    Return the speaker name in a consistence manner.
    If the speaker is N/A or not specified, returns None.
    """
    cleaned = name.strip()
    if cleaned.upper() in ("N/A", ""):
        return None
    return cleaned.upper()
