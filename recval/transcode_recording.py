#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from os import fspath
from pathlib import Path
from hashlib import sha256


def transcode_to_aac(recording_path: Path, destination: Path) -> None:
    """
    Transcodes .wav files to .aac files.
    TODO: Factor this out!
    """
    # TODO: use pydub instead of some gnarly sh command.
    from sh import ffmpeg  # type: ignore

    assert recording_path.exists(), f"Could not stat {recording_path}"
    ffmpeg('-i', fspath(recording_path),
           '-nostdin',
           '-n',  # Do not overwrite existing files
           '-ac', 1,  # Mix to mono
           '-acodec', 'aac',  # Use the AAC codec
           fspath(destination))


def compute_fingerprint(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of the given audio file path.
    """
    assert file_path.suffix == '.wav', f"Expected .wav file; got {file_path}"
    with open(file_path, 'rb') as f:
        return sha256(f.read()).hexdigest()
