#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import pytest  # type: ignore
import tempfile
from uuid import uuid4
from pathlib import Path

from recval.recording import transcode_to_aac


def test_can_transcode_wave_file(wave_file_path: Path,
                                 temporary_directory: Path) -> None:
    destination = temporary_directory / f"{uuid4()}.m4a"
    assert not destination.exists()
    transcode_to_aac(wave_file_path, destination)
    assert destination.exists()


@pytest.fixture
def temporary_directory():
    with tempfile.TemporaryDirectory() as name:
        yield Path(name)
