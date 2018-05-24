#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from hashlib import sha256
from os import fspath
from pathlib import Path
from typing import Union

from pydub import AudioSegment  # type: ignore


def transcode_to_aac(
        recording: Union[Path, AudioSegment],
        destination: Path,
        **kwargs) -> None:
    """
    Transcodes an audio file to an .m4a file.

    Browsers tend to support this AAC-encoded .m4a files:
    https://developer.mozilla.org/en-US/docs/Web/HTML/Supported_media_formats#Browser_compatibility
    """

    if isinstance(recording, Path):
        assert recording.exists(), f"Could not stat {recording}"
        with open(recording, 'rb') as recording_file:
            audio = AudioSegment.from_file(recording_file)
    elif isinstance(recording, AudioSegment):
        audio = recording
    else:
        raise TypeError("Invalid recording: %r" % (recording,))

    assert audio.channels == 1, "Recording is not mono"
    assert len(audio) > 0, "Recording is empty"
    assert destination.suffix == '.m4a', "Don't you want an .m4a file?"

    # This assumes ffmpeg as the backend. This will save
    # a mono audio stream encoded in AAC, in an MP4 container.
    audio.export(destination,
                 format='ipod', codec='aac', **kwargs).\
        close()


def compute_fingerprint(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of the given audio file path.
    """
    assert file_path.suffix == '.wav', f"Expected .wav file; got {file_path}"
    with open(file_path, 'rb') as f:
        return sha256(f.read()).hexdigest()


# TODO: transcode to Opus in Ogg to support libre browsers and basically
# nothing else.
