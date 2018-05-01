#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
Creates the database from scratch.
"""

import sys
from pathlib import Path

from tqdm import tqdm  # type: ignore

from recval.model import db, Recording, Word, Sentence, normalize_utterance

here = Path('.')
SOURCE_AUDIO_PATH = here / 'data' / 'samples'
assert SOURCE_AUDIO_PATH.resolve().is_dir()


if __name__ == '__main__':
    from recval.app import app
    from recval.parse_index import parse

    index_file = Path('./data/samples/index.html')
    assert index_file.exists()

    with app.app_context():
        db.create_all()

        # Assumption is that parse() returns normalized data.
        recordings, _words, _sentences = parse(index_file)
        for crk, en, speaker, recording_path in tqdm(recordings):
            word = Word(translation=normalize_utterance(en),
                        transcription=normalize_utterance(crk))
            recording = Recording.new(phrase=word,
                                      input_file=SOURCE_AUDIO_PATH / recording_path,
                                      speaker=speaker)
            db.session.add(recording)
            db.session.commit()
