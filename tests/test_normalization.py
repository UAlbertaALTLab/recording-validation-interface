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

import pytest  # type: ignore
from hypothesis import given  # type: ignore
from hypothesis.strategies import text  # type: ignore

from librecval.normalization import normalize, to_indexable_form


def test_basic():
    assert "hello" == normalize("  hello ")


def test_nfc():
    assert normalize("   phơ\u0309 ") == normalize("pho\u031B\u0309 ")


@given(text())
def test_idempotence(s):
    """
    Normalizing something that is already normalized should not change it.
    """
    assert normalize(s) == normalize(normalize(s))


# ############################# Indexing tests ############################# #


@pytest.mark.parametrize(
    "original,expected",
    [
        # Indexing MUST ignore vowel length
        ("tânisi", "tanisi"),
        ("tānisi", "tanisi"),
        # Indexing MUST remove extraneous whitespace
        ("    tanisi   ", "tanisi"),
        # Indexing MUST lowercase all the things
        ("TaN'SI", "tanisi"),
        # Indexing MUST treat -iw and -ow as the same.
        ("kiskisiw", "kiskisU"),
        ("kiskisow", "kiskisU"),
        # Indexing MUST treat all forms of vowel elision the same.
        ("tân(i)si", "tanisi"),
        ("mostos(o)wiyâs", "mostosowiyas"),
        ("n(a)môya n'n(i)s(i)tohtên", "namoya ninisitohten"),
        # Indexing MUST ignore hyphens in input
        ("ê-nipat", "enipat"),
        ("ka-kiyâskiskiw", "kakiyaskiskU"),
        # ############################## Regressions ############################ #
        # Addressing a few cases here:
        # https://github.com/UAlbertaALTLab/recording-validation-interface/issues/37#issuecomment-448155202
        ("pwâwîw", "pwawU"),
        ("kostâcinâkosiw", "kostacinakosU"),
        ("iskwêsis", "iskwesis"),
        # ####################################################################### #
        # The following are tests I got from some spell-relax .regex file,
        # deep within giella/.../crk/...
        # i (->) %', # short-i elision
        ("tan'si", "tanisi"),
        # â (->) {ā}, # a + combining macron U+0304
        # ê (->) {ē}, # e + combining macron U+0304
        # î (->) {ī}, # i + combining macron U+0304
        # ô (->) {ō}, # o + combining macron U+0304
        ("a\u0304e\u0304i\u0304o\u0304", "aeio"),
        # Â (->) {Ā}, # A + combining macron U+0304
        # Ê (->) {Ē}, # E + combining macron U+0304
        # Î (->) {Ī}, # I + combining macron U+0304
        # Ô (->) {Ō}, # O + combining macron U+0304
        ("A\u0304E\u0304I\u0304O\u0304", "aeio"),
        # â (->) ā, # a macron
        # ê (->) ē, # e macron
        # î (->) ī, # i macron
        # ô (->) ō, # o macron
        ("\u0101\u0113\u012B\u014d", "aeio"),
        # Â (->) Ā, # A macron
        # Ê (->) Ē, # E macron
        # Î (->) Ī, # I macron
        # Ô (->) Ō, # O macron
        ("\u0100\u0112\u012A\u014C", "aeio"),
        # â (->) {â}, # a + combining circumflex accent U+0302
        # ê (->) {ê}, # e + combining circumflex accent U+0302
        # î (->) {î}, # i + combining circumflex accent U+0302
        # ô (->) {ô}, # o + combining circumflex accent U+0302
        ("a\u0302e\u0302i\u0302o\u0302", "aeio"),
        # Â (->) {Â}, # A + combining circumflex accent U+0302
        # Ê (->) {Ê}, # E + combining circumflex accent U+0302
        # Î (->) {Î}, # I + combining circumflex accent U+0302
        # Ô (->) {Ô}, # O + combining circumflex accent U+0302
        ("A\u0302E\u0302I\u0302O\u0302", "aeio"),
        # # NS 152 materials consistantly (sic) write some vowels as long where Arok's
        # # write them as short. E.G. NS 152 give 'askîy' and Arok gives 'askiy.'
        ("askîy", "askiy"),
        # # Explanation:
        # # lexical side (->) input
        # # Or, in other words:
        # # correct (->) in use out there
    ],
)
def test_index(original, expected):
    assert to_indexable_form(original) == expected
    # Indexing MUST be ASCII
    assert to_indexable_form(original).isprintable()
