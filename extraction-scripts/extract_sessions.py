#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.
# Derived from Praat scripts written by Timothy Mills
#  - extract_items.praat
#  - extract_sessions.praat

import argparse
import logging
from pathlib import Path

from slugify import slugify  # type: ignore

from recval.extract_phrases import RecordingExtractor

logger = logging.getLogger(__name__)
info = logger.info
here = Path('.')

parser = argparse.ArgumentParser()
parser.add_argument('master_directory', default=here, type=Path,
                    help='Where to look for session folders')
parser.add_argument('session_codes', default=here / 'speaker-codes.csv', type=Path,
                    help='A TSV that contains codes for sessions...?', nargs='?')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args()

    # TODO: read session-codes?
    scanner = RecordingExtractor()
    for recording, audio in scanner.scan(root_directory=args.master_directory):
        info("Exporting:\n%s", recording.signature())
        r = recording
        # Export it.
        slug = slugify(f"{r.type}-{r.transcription}-{r.session}-{r.speaker}-{r.timestamp}",
                       to_lower=True)
        audio.export(str(Path('/tmp') / f"{slug}.wav"))
