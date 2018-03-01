#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos/University of Alberta.
# All rights reserved.

"""
Try to parse the index.html file.
"""

from pathlib import Path
from unicodedata import normalize
from warnings import warn
from typing import Tuple, List, Set, Dict

from bs4 import BeautifulSoup  # type: ignore
# TODO: use langid


def parse(index_filename: Path) -> Tuple[Set, Dict, List]:
    base_dir = index_filename.parent

    words = {}  # type: ignore
    sentences = []  # type: ignore
    recordings = set()  # type: ignore

    print("Parsing...")
    with open(index_filename) as fp:
        # lxml handles the spurious </tr> tags appropriately.
        soup = BeautifulSoup(fp, 'lxml')
    print("Done.")

    # Get the big table of recordings.
    big_table = soup.table

    def clean_phrase(term: str) -> str:
        """
        Cleans up a pharse (sentence or word).
        """
        return normalize('NFC', term.strip())

    def parse_sentence(sentence_column):
        raw_setences = sentence_column.find_all('tr')
        sentences = []
        for row in raw_setences:
            contents = row.contents
            crk = clean_phrase(contents[0].string or '')
            en = clean_phrase(contents[1].string or '')

            if not crk:
                warn(f'No transcription available: {row}. Skipping.')
                continue
            if not en:
                warn(f'No translation available: {row}. Skipping.')
                continue

            # Look at the <a> -- it contains the speaker AND a link to the
            # recording
            assert len(contents[2].find_all('a')) == 1
            anchor = contents[2].a
            speaker = clean_phrase(anchor.string or '')

            if not speaker:
                warn(f'No speaker for sentence: "{crk}"')

            # Get the recording path. Make sure it exists, and escape it!
            # TODO: factor out as function.
            raw_recording_path = str(anchor['href'] or '')
            assert raw_recording_path
            assert (base_dir / raw_recording_path).exists()
            recording_path = raw_recording_path
            recording = (crk, en, speaker, recording_path)

            sentences.append(
                (crk, en, speaker, recording_path)
            )

            recordings.add(recording)

        return sentences

    def parse_words(word_column):
        for anchor in word_column.find_all('a'):
            speaker = clean_phrase(anchor.string or '')

            # Get the recording path. Make sure it exists, and escape it!
            raw_recording_path = str(anchor['href'] or '')
            assert raw_recording_path
            if not (base_dir / raw_recording_path).exists():
                # So there are files that start with: otiti*
                # but then I guess the encoding is denormalized and this causes
                # issues both on my Mac and on the Linux machine... :/
                #
                # The result is, even though they are _there_, they are
                # irretrivable by conventional means. The other way to get them is
                # by looking them up by inode. Yay.
                #
                # Try this on the Linux box:
                #   ls -li samples/words/otit* | grep -E '[^a-zA-Z0-9_-. ]'
                warn(f'No audio file found: "{raw_recording_path}". Skipping')
                continue
            recording_path = raw_recording_path
            yield speaker, recording_path

    # Each row in the table is either a word or a sentence.
    for row in big_table:
        assert row.name == 'tr'

        # Get columns. There should be exactly four.
        columns = [
            col for col in row.children
            if hasattr(col, 'name') and col.name == 'td'
        ]
        assert len(columns) == 4

        # Sometimes these are swapped --- watch out!
        crk = clean_phrase(columns[0].string or '')
        en = clean_phrase(columns[1].string or '')

        is_word = bool(columns[2].contents)
        is_sentence = bool(columns[3].contents)

        if is_sentence:
            sentences.append((crk, en, parse_sentence(columns[3])))

        if is_word:
            if not crk:
                warn(f'No transcription available: {row}. Skipping.')
                continue
            if not en:
                warn(f'No translation available: {row}. Skipping.')
                continue
            for speaker, recording_path in parse_words(columns[2]):
                recording = (crk, en, speaker, recording_path)
                recordings.add(recording)
                # XXX: hash is only meaninful in THIS PROCESS of Python!
                words[crk] = (crk, en, hash(recording))

    return recordings, words, sentences


if __name__ == '__main__':
    index_filename = Path('data/samples/index.html')
    recordings, words, sentences = parse(index_filename)
    from pprint import pprint
    pprint(words)
