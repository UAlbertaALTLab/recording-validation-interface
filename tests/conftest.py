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
Fixtures and magic for pytests.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest  # type: ignore

# Where are fixture files located?
fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture
def _temporary_data_directory():
    """
    Yields an absolute path to a temporary data directory for storing
    databases and other files.
    """
    with TemporaryDirectory() as tempdir_name:
        path = Path(tempdir_name).resolve()
        yield path


@pytest.fixture
def wave_file_path():
    """
    A recording saying "acimosis" (puppy), for use in test cases.
    """
    test_wav = fixtures_dir / "test.wav"
    assert test_wav.exists()
    return test_wav


@pytest.fixture
def metadata_csv_file():
    """
    Returns a file-like object that is some sample metadata, as downloaded
    from Google Sheets.
    """
    with open(fixtures_dir / "test_metadata.csv") as csvfile:
        yield csvfile


@pytest.fixture
def skip_metadata_csv_file():
    """
    Returns a file-like object that is some sample metadata, with !SKIP, as downloaded
    from Google Sheets.
    """
    with open(fixtures_dir / "test_metadata_skip.csv") as csvfile:
        yield csvfile


@pytest.fixture
def rename_metadata_csv_file():
    """
    Returns a file-like object that is some sample metadata, with a session rename, as downloaded
    from Google Sheets.
    """
    with open(fixtures_dir / "test_metadata_rename.csv") as csvfile:
        yield csvfile
