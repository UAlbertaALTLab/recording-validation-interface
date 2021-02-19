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
from hashlib import sha256

import logme  # type: ignore
from typing_extensions import Literal

from librecval.extract_phrases import AudioSegment, RecordingExtractor, Segment
from librecval.recording_session import parse_metadata, SessionID, SessionMetadata
from librecval.transcode_recording import transcode_to_aac

from validation.models import RecordingSession, Recording, TranscriptionFile


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


class KitchenSink:
    def __init__(self, info, audio, metadata):
        self.info = info
        self.audio = audio
        self.metadata = metadata

        self.transcription_hash = compute_transcription_hash(info.annotation_path)
        self.session_hash = compute_session_hash(metadata[info.session])
        self.recording_hash = compute_recording_hash(audio)

    def compute_sha256hash(self):
        return self.info.compute_sha256hash()

    @property
    def speaker(self):
        return self.info.speaker

    @property
    def session(self):
        return self.info.session

    @property
    def cree_transcription(self):
        return self.info.cree_transcription

    @property
    def english_translation(self):
        return self.info.english_translation

    @property
    def type(self):
        return self.info.type

    @property
    def start(self):
        return self.info.start

    @property
    def quality(self):
        return self.info.quality

    @property
    def comment(self):
        return self.info.comment

    @property
    def annotation_path(self):
        return self.info.annotation_path


ImportRecording = Callable[[KitchenSink, Path], None]


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
    segments = [
        KitchenSink(info, audio, metadata)
        for info, audio in ex.scan(root_directory=directory)
    ]
    segments_to_import = []

    for segment in segments:
        if should_import(segment):
            segments_to_import.append(segment)

    for segment in segments_to_import:
        try:
            recording_path = save_recording(
                dest, segment.info, segment.audio, recording_format
            )
        except RecordingError:
            logger.exception("Exception while saving recording; skipping.")
        else:
            import_recording(segment, recording_path)


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


def compute_session_hash(metadata: SessionMetadata):
    # takes a single row from the metadata and hashes it
    metadata_to_hash = repr(metadata)
    return sha256(metadata_to_hash.encode("UTF-8")).hexdigest()


def compute_recording_hash(audio: AudioSegment):
    # takes the raw data from the AudioSegment and hashes it
    return sha256(audio.raw_data).hexdigest()


def compute_transcription_hash(annotation_path: Path):
    return sha256(annotation_path.read_bytes()).hexdigest()


@logme.log
def should_import(segment: KitchenSink, logger=None):
    # Checks if the segment hash has changed or does not exist
    # Returns True if needs to be imported

    try:
        rec_session = RecordingSession.objects.get(id=segment.session)
    except RecordingSession.DoesNotExist:
        logger.info(f"Recording session does not exist: {segment.session}")
        return True
    if rec_session.session_hash != segment.session_hash:
        logger.info("Recording session hash doesn't match")
        return True

    try:
        # The recording uses the transcription_hash as its ID
        recording = Recording.objects.get(id=segment.compute_sha256hash())
    except Recording.DoesNotExist:
        logger.info(f"Recording does not exist")
        return True
    if recording.recording_hash != segment.recording_hash:
        logger.info("Recording hash doesn't match")
        return True

    try:
        transcription = TranscriptionFile.objects.get(
            file_name=str(segment.annotation_path.resolve())
        )
    except TranscriptionFile.DoesNotExist:
        logger.info(
            f"Transcription file does not exist: {str(segment.annotation_path.resolve())}"
        )
        return True
    if transcription.file_hash != segment.transcription_hash:
        logger.info("Transcription file hash doesn't match")
        return True

    logger.info("Don't import")
    return False


def delete_entry(entry):
    # TODO: this
    # "Update" an entry that's already in the DB but has changed a little
    pass
