#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import pytest  # type: ignore
import tempfile
from uuid import uuid4
from pathlib import Path

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


@pytest.fixture
def temporary_directory():
    with tempfile.TemporaryDirectory() as name:
        yield Path(name)
