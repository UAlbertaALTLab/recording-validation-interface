#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
Creates the database from scratch.
"""

import sys
from pathlib import Path
from hashlib import sha256


def fingerprint(file_path: Path) -> str:
    with open(file_path, 'rb') as f:
        return sha256(f.read()).hexdigest()


base_path = Path('.').parent / 'data' / 'samples'
assert base_path.resolve().is_dir()


if __name__ == '__main__':
    from recval.app import db, Recording, Word, Sentence, normalize_utterance
    from recval.parse_index import parse

    index_file = Path('./data/samples/index.html')
    assert index_file.exists()

    db.create_all()

    # Assumption is that parse() returns normalized data.
    recordings, _words, _sentences = parse(index_file)
    for crk, en, speaker, recording_path in recordings:
        word = Word(translation=normalize_utterance(en),
                    transcription=normalize_utterance(crk))

        recording = Recording(fingerprint=fingerprint(base_path / recording_path),
                              speaker=speaker,
                              phrase=word)
        db.session.add(recording)
        db.session.commit()
