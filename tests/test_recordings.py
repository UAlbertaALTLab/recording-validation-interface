#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import warnings
import tempfile
from uuid import uuid4
from pathlib import Path

import pytest  # type: ignore
from pydub.generators import Square  # type: ignore

from recval.transcode_recording import transcode_to_aac


def test_can_transcode_wave_file(wave_file_path: Path,
                                 temporary_directory: Path) -> None:
    destination = temporary_directory / f"{uuid4()}.m4a"

    # Check that transcoding creates a new file, at least.
    assert not destination.exists()
    transcode_to_aac(wave_file_path, destination)
    assert destination.exists()

    # Check that it's has an MP4 header, at least.
    blob = destination.read_bytes()
    assert b'ftyp' == blob[4:8]
    assert b'M4A ' == blob[8:12]


def test_can_transcode_audio_in_memory(temporary_directory: Path) -> None:
    # Transcode a file in memory.
    recording = Square(441).to_audio_segment()
    destination = temporary_directory / f"{uuid4()}.m4a"

    assert not destination.exists()
    transcode_to_aac(recording, destination)
    assert destination.exists()

    # Check that it's has an MP4 header, at least.
    blob = destination.read_bytes()
    assert b'ftyp' == blob[4:8]
    assert b'M4A ' == blob[8:12]


def test_can_recover_metadata(wave_file_path: Path,
                              temporary_directory: Path) -> None:
    destination = temporary_directory / f"{uuid4()}.m4a"

    # Check that transcoding creates a new file, at least.
    assert not destination.exists()
    creation_time = "2015-12-03"
    acimosis = "ᐊᒋᒧᓯᐢ"
    transcode_to_aac(wave_file_path, destination, tags=dict(
        title=acimosis,
        performer="SPEAKER",
        album=creation_time,
        language="crk",
        creation_time=creation_time,
        year=2015
    ))
    assert destination.exists()

    # Check that it's has an MP4 header, at least.
    blob = destination.read_bytes()
    assert acimosis.encode('UTF-8') in blob
    assert creation_time.encode('UTF-8') in blob
    if b'crk' not in blob:
        warnings.warn("Did not find language in .m4a file!")
    if b'SPEAKER' not in blob:
        warnings.warn("Did not find speaker in .m4a file!")
    assert b'2015' in blob


@pytest.fixture
def temporary_directory():
    with tempfile.TemporaryDirectory() as name:
        yield Path(name)
