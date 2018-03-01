#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos/University of Alberta.
# All rights reserved.

"""
Try to parse the index.html file.
"""

from pathlib import Path
from unicodedata import normalize
from urllib.parse import quote
from warnings import warn

from bs4 import BeautifulSoup  # type: ignore
# TODO: use langid


index_filename = Path('data/samples/index.html')


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

        # Look at the <a> -- it contains the speaker AND a link to the
        # recording
        assert len(contents[2].find_all('a')) == 1
        anchor = contents[2].a
        speaker = clean_phrase(anchor.string or '')
        recording_path = quote(str(anchor['href']))
        sentences.append(
            (crk, en, speaker, recording_path)
        )
    return sentences


def parse_word(word_column):
    raise NotImplementedError


words = []  # type: ignore
sentences = []  # type: ignore


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
        assert not is_word
        sentences.append((crk, en, parse_sentence(columns[3])))

    try:
        if is_word:
            words.append(
                parse_word(columns[2])
            )
    except NotImplementedError:
        break

print(sentences)
