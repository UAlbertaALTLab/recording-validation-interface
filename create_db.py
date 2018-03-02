#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
Creates the database from scratch.
"""

import sys
from pathlib import Path


if __name__ == '__main__':
    from recval.app import db, Recording
    from recval.parse_index import parse

    index_file = Path('./data/samples/index.html')
    assert index_file.exists()

    db.create_all()

    if 'create' in sys.argv[1:]:
        # Assumption is that parse() returns normalized data.
        recordings, _words, _sentences = parse(index_file)
        for crk, en, speaker, recording_path in recordings:
            db.session.add(
                Recording(file_path=recording_path,
                          translation=en,
                          transcription=crk,
                          speaker=speaker)
            )
        db.session.commit()
