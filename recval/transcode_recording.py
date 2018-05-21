#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from os import fspath
from pathlib import Path
from hashlib import sha256
from typing import Union

from pydub import AudioSegment  # type: ignore


def transcode_to_aac(recording: Union[Path, AudioSegment], destination: Path) -> None:
    """
    Transcodes an audio file to an .m4a file.

    Browsers tend to support this AAC-encoded .m4a files:
    https://developer.mozilla.org/en-US/docs/Web/HTML/Supported_media_formats#Browser_compatibility
    """

    # TODO: use pydub instead of some gnarly sh command.
    from sh import ffmpeg  # type: ignore

    if isinstance(recording, Path):
        assert recording.exists(), f"Could not stat {recording}"
        audio = AudioSegment.from_file(fspath(recording))
    elif isinstance(recording, AudioSegment):
        audio = recording
    else:
        raise TypeError("Invalid recording: %r" % (recording,))

    assert audio.channels == 1, "Recording is not mono"
    assert len(audio) > 0, "Recording is blank"
    assert destination.suffix == '.m4a', "Don't toy want an .m4a file?"

    # This assumes ffmpeg as the backend. This will save
    # a mono audio stream encoded in AAC, in an MP4 container.
    audio.export(fspath(destination),
                 format='ipod', codec='aac')


def compute_fingerprint(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of the given audio file path.
    """
    assert file_path.suffix == '.wav', f"Expected .wav file; got {file_path}"
    with open(file_path, 'rb') as f:
        return sha256(f.read()).hexdigest()


# https://www.ffmpeg.org/doxygen/3.2/group__metadata__api.html
"""
tags=dict(title=info.transcription,
performer=info.speaker,
album=info.session,
language="crk",
creation_time=f"{info.session.date:%Y-%m-%d}",
year=info.session.year),
"""

"""
ffmpeg('-i', fspath(recording_path),
       '-nostdin',
       '-n',  # Do not overwrite existing files
       '-ac', 1,  # Mix to mono
       '-acodec', 'aac',  # Use the AAC codec
       fspath(destination))
"""
