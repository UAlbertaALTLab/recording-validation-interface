#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
Creates the database from scratch.
"""

import sys
from os import fspath
from pathlib import Path
from typing import Dict

from tqdm import tqdm  # type: ignore

from recval.extract_phrases import RecordingExtractor, RecordingInfo
from recval.model import Phrase, Recording, Sentence, Word, db

cache: Dict[RecordingInfo, Phrase] = {}


def make_phrase(info: RecordingInfo) -> Phrase:
    if info in cache:
        return cache[info]
    if info.type == 'word':
        p = Word(transcription=info.transcription,
                 translation=info.translation)
    elif info.type == 'sentence':
        p = Sentence(transcription=info.transcription,
                     translation=info.translation)
    else:
        raise Exception(f"Unexpected phrase type: {info.type!r}")
    cache[info] = p
    return p


if __name__ == '__main__':
    from recval.app import app
    directory = Path(sys.argv[1])
    assert directory.resolve().is_dir()

    ex = RecordingExtractor()
    with app.app_context():
        # Create the schema.
        db.create_all()
        dest = app.config['TRANSCODED_RECORDINGS_PATH']
        assert dest.resolve().is_dir()

        # Insert each thing found.
        for info, audio in tqdm(ex.scan(root_directory=directory)):
            fingerprint = info.compute_sha256hash()
            recording_path = dest / f"{fingerprint}.aac"
            # Export a mono AAC file with metadata.
            if not recording_path.exists():
                audio.export(fspath(recording_path),
                             tags=dict(title=info.transcription,
                                       artist=info.speaker,
                                       album=info.session,
                                       year=info.session.year),
                             # So that windows explorer will display the tags
                             # Source: https://superuser.com/a/453133/711047
                             id3v2_version='3',
                             parameters=['-ac', '1'])
            phrase = make_phrase(info)
            recording = Recording.new(phrase=phrase,
                                      input_file=recording_path,
                                      speaker=info.speaker,
                                      fingerprint=fingerprint)
            db.session.add(recording)
            db.session.commit()
