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

"""
Tests for extracting and handling the metadata.
"""

from librecval.recording_session import (Location, SessionID, SessionParseError,
                                         TimeOfDay, parse_metadata)


def test_parse_csv(metadata_csv_file) -> None:
    """
    Parse the metadata file and fetching some speaker codes using it as a
    dictionary.
    """
    metadata = parse_metadata(metadata_csv_file)
    # Refer to the tests/fixtures/test_metadata.csv for correct numbers.
    assert 7 == len(metadata)
    example_session_id = SessionID.from_name('2015-04-15-PM-___-_')
    assert example_session_id in metadata
    session = metadata[example_session_id]
    assert ('LOU', 'MAR', 'JER') == (session[2], session[3], session[4])


def test_metadata_special_codes(skip_metadata_csv_file) -> None:
    """
    Parses metadata with special codes.
    """
    metadata = parse_metadata(skip_metadata_csv_file)
    # Refer to the tests/fixtures/test_metadata_skip.csv for correct numbers.
    # There should be three data rows, but one is marked !SKIP
    assert SessionD.parse_dirty('2014-12-09') in metadata
    assert SessionID.parse_dirty('2014-12-10') in metadata
    assert SessionID.parse_dirty('2014-12-16') not in metadata
    assert 2 == len(metadata)
