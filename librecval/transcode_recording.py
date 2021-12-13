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

from pathlib import Path
from typing import Union

from pydub import AudioSegment  # type: ignore


def transcode_to_aac(
    recording: Union[Path, AudioSegment], destination: Path, **kwargs
) -> None:
    """
    Transcodes an audio file to an .m4a file.

    Browsers tend to support this AAC-encoded .m4a files:
    https://developer.mozilla.org/en-US/docs/Web/HTML/Supported_media_formats#Browser_compatibility
    """

    if isinstance(recording, Path):
        assert recording.exists(), f"Could not stat {recording}"
        with open(recording, "rb") as recording_file:
            audio = AudioSegment.from_file(recording_file)
    elif isinstance(recording, AudioSegment):
        audio = recording
    else:
        raise TypeError("Invalid recording: %r" % (recording,))

    assert audio.channels == 1, f"Recording is not mono, has {audio.channels} channels"
    assert len(audio) > 0, "Recording is empty"
    assert destination.suffix == ".m4a", "Don't you want an .m4a file?"

    # This assumes ffmpeg as the backend. This will save
    # a mono audio stream encoded in AAC, in an MP4 container.
    audio.export(
        destination,
        format="ipod",
        codec="aac",
        **kwargs,
        # On Ubuntu's ffmpeg, the aac codec is experimental,
        # so enable experimental codecs!
        parameters=["-strict", "-2"],
    ).close()


# TODO: transcode to Opus in Ogg to support libre browsers and basically
# nothing else.
