#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
Creates the database from scratch.

This is script is really ugly. I'm sorry :C.
"""

import sys
from os import fspath
from pathlib import Path
from typing import Dict, Any

from tqdm import tqdm  # type: ignore

from recval.extract_phrases import RecordingExtractor, RecordingInfo
from recval.model import Phrase, Recording, Sentence, Word, VersionedString
from recval.database import init_db


info2phrase = {}  # type: ignore


def make_phrase(info: RecordingInfo) -> Phrase:
    """
    Tries to fetch an existing phrase from the database, or else creates a
    new one.
    """

    key = info.type, info.transcription

    if key in info2phrase:
        # Look up the phrase.
        phrase_id = info2phrase[key]
        return Phrase.query.filter_by(id=phrase_id).one()

    # Otherwise, create a new phrase.
    transcription = fetch_versioned_string(info.transcription)
    translation = fetch_versioned_string(info.translation)
    if info.type == 'word':
        p = Word(transcription_meta=transcription,
                 translation_meta=translation)
    elif info.type == 'sentence':
        p = Sentence(transcription_meta=transcription,
                     translation_meta=translation)
    else:
        raise Exception(f"Unexpected phrase type: {info.type!r}")
    assert p.id is None
    db.session.add(p)
    db.session.commit()
    assert p.id is not None
    info2phrase[key] = p.id
    return p


def fetch_versioned_string(value: str) -> VersionedString:
    """
    Get a versioned string.
    """
    res = VersionedString.query.filter_by(value=value).all()
    assert len(res) in (0, 1)
    if res:
        return res[0]
    v = VersionedString.new(value=value, author_name='<unknown>')
    return v


if __name__ == '__main__':
    from recval.app import app
    directory = Path(sys.argv[1])
    assert directory.resolve().is_dir()

    ex = RecordingExtractor()
    with app.app_context():
        dest = app.config['TRANSCODED_RECORDINGS_PATH']
        assert dest.resolve().is_dir()

        # Create the schema.
        db = init_db()

        # Insert each thing found.
        for info, audio in tqdm(ex.scan(root_directory=directory)):
            fingerprint = info.compute_sha256hash()
            recording_path = dest / f"{fingerprint}.m4a"
            if not recording_path.exists():
                # Export a mono AAC file with metadata.
                # See: https://superuser.com/a/1055816/711047
                audio.set_channels(1).\
                    export(fspath(recording_path),
                           format='adts', codec='aac')
                           # tags=dict(title=info.transcription,
                           #           artist=info.speaker,
                           #           album=info.session,
                           #           year=info.session.year),
                           # id3v2_version='3')
                assert recording_path.exists()
            phrase = make_phrase(info)
            recording = Recording.new(phrase=phrase,
                                      input_file=recording_path,
                                      speaker=info.speaker,
                                      fingerprint=fingerprint)
            db.session.add(recording)
            db.session.commit()
