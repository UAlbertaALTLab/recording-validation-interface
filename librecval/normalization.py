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

import re
import unicodedata


# A translation table to convert macrons to cicumflexes in lowercase, NFC
# strings.
MACRON_TO_CIRCUMFLEX = str.maketrans('ēīōā', 'êîôâ')


def nfc(utterance: str) -> str:
    return unicodedata.normalize('NFC', utterance)


def normalize(utterance: str) -> str:
    r"""
    Normalizes utterances (translations, transcriptions, etc.)
    """
    return unicodedata.normalize('NFC', utterance.strip())


def normalize_sro(utterance: str) -> str:
    """
    Normalizes Plains Cree text written in the standard Roman orthography.

    The following are the normalizations applied:

    Lower-cased:

    >>> normalize_sro('Maskêkosihk')
    'maskêkosihk'

    No extraneous whitespace on either edge of the string:

    >>> normalize_sro('  maskêkosihk ')
    'maskêkosihk'

    Exactly one U+0020 SPACE character between words:

    >>> normalize_sro('nisto  nêwo  kapakihtikta    nipiy')
    'nisto nêwo kapakihtikta nipiy'

    All <ê> are long:

    >>> normalize_sro('kecikwasakew')
    'kêcikwasakêw'
    """

    # TODO: (i)-elision, (o)-elision, '-elision, ’-elision
    # TODO: nin's'tohtên
    # TODO: nin(i)s(i)tohtên

    utterance = nfc(utterance).\
        strip().\
        lower().\
        replace('e', 'ê').\
        translate(MACRON_TO_CIRCUMFLEX)

    # Ensure hyphens are consistently exactly one hyphen-minus character.
    utterance = re.sub(r'\s+-\s+', '-', utterance)
    # Ensure there are exactly single spaces between words
    return re.sub(r'\s+', ' ', utterance)


def to_indexable_form(text: str) -> str:
    """
    Converts text in SRO to a string to an indexable (searchable) form.
    """

    # Decompose the text...
    text = unicodedata.normalize('NFD', text)
    # So that we can rip off combining accents (e.g., circumflex or macron)
    text = re.sub(r"[\u0300-\u03ff]", '', text)
    # From now on, we operate on lowercase text only.
    text = text.lower()
    # Undo short-i elision
    text = re.sub(r"(?<=[qwrtpsdfghjklzxcvbnm])'", "i", text)
    return text
