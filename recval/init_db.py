#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Temporary place for database creation glue code.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from recval.extract_phrases import RecordingExtractor, RecordingInfo
from recval.transcode_recording import transcode_to_aac
from recval.recording_session import parse_metadata


ImportRecording = Callable[[RecordingInfo, str, Path], None]


def initialize(
        directory: Path,
        transcoded_recordings_path: str,
        repository_root: Path,
        import_recording: ImportRecording,
        ) -> None:
    """
    Creates the database from scratch.
    """

    dest = Path(transcoded_recordings_path)
    metadata_filename = repository_root / 'etc' / 'metadata.csv'

    assert directory.resolve().is_dir()
    assert dest.resolve().is_dir()
    assert metadata_filename.resolve().is_file()

    with open(metadata_filename) as metadata_csv:
        metadata = parse_metadata(metadata_csv)

    # Insert each thing found.
    # TODO: use click.progressbar()?
    logging.basicConfig(level=logging.INFO)
    ex = RecordingExtractor(metadata)
    for info, audio in ex.scan(root_directory=directory):
        rec_id = info.compute_sha256hash()
        recording_path = dest / f"{rec_id}.m4a"
        if not recording_path.exists():
            # https://www.ffmpeg.org/doxygen/3.2/group__metadata__api.html
            transcode_to_aac(audio, recording_path, tags=dict(
                title=info.transcription,
                performer=info.speaker,
                album=info.session,
                language="crk",
                creation_time=f"{info.session.date:%Y-%m-%d}",
                year=info.session.year
            ))
            assert recording_path.exists()
        import_recording(info, rec_id, recording_path)
