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
MACRON_TO_CIRCUMFLEX = str.maketrans("ēīōā", "êîôâ")
# Translates apostrophes and pretty quotes to <i>.
QUOTE_TO_SHORT_I = str.maketrans("'’", "ii")
# Removes long vowel diacritics on NORMALIZED SRO!
REMOVE_LONG_VOWELS = str.maketrans("êîôâ", "eioa")


def nfc(utterance: str) -> str:
    return unicodedata.normalize("NFC", utterance)


def normalize(utterance: str) -> str:
    r"""
    Normalizes utterances (translations, transcriptions, etc.)
    """
    return unicodedata.normalize("NFC", utterance.strip())


def normalize_sro(utterance: str) -> str:
    """
    Normalizes Plains Cree utterances written in the standard Roman orthography.

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

    Undo short-i elision (with apostrophe or quotes):

    >>> normalize_sro("tân’si/tân'si")
    'tânisi/tânisi'

    Undo vowel elision using parentheses:

    >>> normalize_sro("mostos(o)wiyâs/nin(i)s(i)tohtên")
    'mostosowiyâs/ninisitohtên'
    """

    utterance = (
        normalize_phrase(utterance)
        .lower()
        .replace("e", "ê")
        .translate(MACRON_TO_CIRCUMFLEX)
        .translate(QUOTE_TO_SHORT_I)
    )

    utterance = re.sub(r"[(]([ioa])[)]", r"\1", utterance)

    # Ensure there are exactly single spaces between words
    return re.sub(r"\s+", " ", utterance)


def normalize_phrase(utterance: str) -> str:
    """
    Basic normalization for all phrases in any language:

    >>> normalize_phrase("  Brian n't'siyihka\N{COMBINING MACRON}son  ")
    "Brian n't'siyihkāson"
    """
    return nfc(utterance).strip()


def to_indexable_form(text: str) -> str:
    """
    Converts text in SRO to a string to an indexable (searchable) form.

    A note about -iw and -ow endings.

    Since sources tend to mix between spelling these in either -iw or -ow
    (and it's pronouned more like /u/ in either case), they are both
    normalized to <U>, which would never normally appear in SRO text.
    """

    text = normalize_sro(text).replace("-", "").translate(REMOVE_LONG_VOWELS)

    # Undo short-i elision
    text = re.sub(r"(?<=[qwrtpsdfghjklzxcvbnm])'", "i", text)
    # -iw/-ow -> U (people spell it two different ways but pronounce it /u/)
    text = re.sub(r"[oi]w\b", "U", text)

    return text
