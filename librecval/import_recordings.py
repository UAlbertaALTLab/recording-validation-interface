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
Temporary place for database creation glue code.
"""

import os
from pathlib import Path
from typing import Callable

import logme  # type: ignore
from typing_extensions import Literal

from librecval.extract_phrases import AudioSegment, RecordingExtractor, Segment
from librecval.recording_session import parse_metadata
from librecval.transcode_recording import transcode_to_aac

ImportRecording = Callable[[Segment, Path], None]

# TODO: create report with emoji
#
# ✅ 2016-04-23AM-OFF - 3 text grids, 230 words
# ⚠️  2016-05-06AM-KCH - could not link text grids to audio
# ⚠️  2016-03-06AM-OFF - could not find mettadata


class RecordingError(Exception):
    """
    The error that gets raised if something bad happens with the recording.
    """


Format = Literal["wav", "m4a"]


@logme.log
def initialize(
    directory: Path,
    transcoded_recordings_path: str,
    metadata_filename: Path,
    import_recording: ImportRecording,
    recording_format: Format = "m4a",
    logger=None,
) -> None:
    """
    Creates the database from scratch.
    """

    dest = Path(transcoded_recordings_path)

    assert directory.resolve().is_dir(), directory
    assert (
        dest.resolve().is_dir()
    ), f"audio destination is not a folder: {dest.resolve()}"
    assert metadata_filename.resolve().is_file(), metadata_filename

    with open(metadata_filename) as metadata_csv:
        metadata = parse_metadata(metadata_csv)

    # Insert each thing found.
    ex = RecordingExtractor(metadata)
    for info, audio in ex.scan(root_directory=directory):
        try:
            recording_path = save_recording(dest, info, audio, recording_format)
        except RecordingError:
            logger.exception("Exception while saving recording; skipping.")
        else:
            import_recording(info, recording_path)


@logme.log
def save_recording(
    dest: Path,
    info: Segment,
    audio: AudioSegment,
    recording_format: Format = "m4a",
    logger=None,
) -> Path:
    rec_id = info.compute_sha256hash()
    recording_path = dest / f"{rec_id}.{recording_format}"
    if recording_path.exists():
        logger.warn("Already exists, not transcoding: %s", recording_path)
        return recording_path

    if len(audio) == 0:
        raise RecordingError(f"Recording empty for {info!r}")

    # https://www.ffmpeg.org/doxygen/3.2/group__metadata__api.html
    logger.debug("Writing audio to %s", recording_path)
    if recording_format == "m4a":
        transcode_to_aac(
            audio,
            recording_path,
            tags=dict(
                title=info.cree_transcription,
                artist=info.speaker,
                album=info.session,
                language="crk",
                creation_time=f"{info.session.date:%Y-%m-%d}",
                year=info.session.year,
            ),
        )
    else:
        audio.export(os.fspath(recording_path), format="wav")
    assert recording_path.exists()
    return recording_path
