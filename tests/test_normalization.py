#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import pytest  # type: ignore
from hypothesis import given  # type: ignore
from hypothesis.strategies import text  # type: ignore

from recval.normalization import normalize, to_indexable_form


def test_basic():
    assert 'hello' == normalize("  hello ")


def test_nfc():
    assert normalize("   phơ\u0309 ") == normalize("pho\u031B\u0309 ")


@given(text())
def test_idempotence(s):
    """
    Normalizing something that is already normalized should not change it.
    """
    assert normalize(s) == normalize(normalize(s))


# ############################# Indexing tests ############################# #

def test_index():
    # i (->) %', # short-i elision
    assert "tanisi" == to_indexable_form("tan'si")

    # â (->) {ā}, # a + combining macron U+0304
    # ê (->) {ē}, # e + combining macron U+0304
    # î (->) {ī}, # i + combining macron U+0304
    # ô (->) {ō}, # o + combining macron U+0304
    assert "aeio" == to_indexable_form("a\u0304e\u0304i\u0304o\u0304")

    # Â (->) {Ā}, # A + combining macron U+0304
    # Ê (->) {Ē}, # E + combining macron U+0304
    # Î (->) {Ī}, # I + combining macron U+0304
    # Ô (->) {Ō}, # O + combining macron U+0304
    assert "aeio" == to_indexable_form("A\u0304E\u0304I\u0304O\u0304")

    # â (->) ā, # a macron
    # ê (->) ē, # e macron
    # î (->) ī, # i macron
    # ô (->) ō, # o macron
    assert "aeio" == to_indexable_form("\u0101\u0113\u012B\u014d")

    # Â (->) Ā, # A macron
    # Ê (->) Ē, # E macron
    # Î (->) Ī, # I macron
    # Ô (->) Ō, # O macron
    assert "aeio" == to_indexable_form("\u0100\u0112\u012A\u014C")

    # â (->) {â}, # a + combining circumflex accent U+0302
    # ê (->) {ê}, # e + combining circumflex accent U+0302
    # î (->) {î}, # i + combining circumflex accent U+0302
    # ô (->) {ô}, # o + combining circumflex accent U+0302
    assert "aeio" == to_indexable_form("a\u0302e\u0302i\u0302o\u0302")

    # Â (->) {Â}, # A + combining circumflex accent U+0302
    # Ê (->) {Ê}, # E + combining circumflex accent U+0302
    # Î (->) {Î}, # I + combining circumflex accent U+0302
    # Ô (->) {Ô}, # O + combining circumflex accent U+0302
    assert "aeio" == to_indexable_form("A\u0302E\u0302I\u0302O\u0302")

    # NS 152 materials consistantly write some vowels as long where Arok's
    # write them as short. E.G. NS 152 give 'askîy' and Arok gives 'askiy.'
    assert "askiy" == to_indexable_form("askîy")

    # # Explanation:
    # # lexical side (->) input
    # # Or, in other words:
    # # correct (->) in use out there
