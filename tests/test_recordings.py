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

import warnings
import tempfile
from uuid import uuid4
from pathlib import Path

import pytest  # type: ignore
from pydub.generators import Square  # type: ignore

from librecval.transcode_recording import transcode_to_aac


def test_can_transcode_wave_file(
    wave_file_path: Path, temporary_directory: Path
) -> None:
    destination = temporary_directory / f"{uuid4()}.m4a"

    # Check that transcoding creates a new file, at least.
    assert not destination.exists()
    transcode_to_aac(wave_file_path, destination)
    assert destination.exists()

    # Check that it's has an MP4 header, at least.
    blob = destination.read_bytes()
    assert b"ftyp" == blob[4:8]
    assert b"M4A " == blob[8:12]


def test_can_transcode_audio_in_memory(temporary_directory: Path) -> None:
    # Transcode a file in memory.
    recording = Square(441).to_audio_segment()
    destination = temporary_directory / f"{uuid4()}.m4a"

    assert not destination.exists()
    transcode_to_aac(recording, destination)
    assert destination.exists()

    # Check that it's has an MP4 header, at least.
    blob = destination.read_bytes()
    assert b"ftyp" == blob[4:8]
    assert b"M4A " == blob[8:12]


def test_can_recover_metadata(wave_file_path: Path, temporary_directory: Path) -> None:
    destination = temporary_directory / f"{uuid4()}.m4a"

    # Check that transcoding creates a new file, at least.
    assert not destination.exists()
    creation_time = "2015-12-03"
    acimosis = "ᐊᒋᒧᓯᐢ"
    transcode_to_aac(
        wave_file_path,
        destination,
        tags=dict(
            title=acimosis,
            artist="SPEAKER",
            album=creation_time,
            language="crk",
            creation_time=creation_time,
            year=2015,
        ),
    )
    assert destination.exists()

    # Check that it's has an MP4 header, at least.
    blob = destination.read_bytes()
    assert acimosis.encode("UTF-8") in blob
    assert creation_time.encode("UTF-8") in blob
    assert b"SPEAKER" in blob
    assert b"2015" in blob


@pytest.fixture
def temporary_directory():
    with tempfile.TemporaryDirectory() as name:
        yield Path(name)
