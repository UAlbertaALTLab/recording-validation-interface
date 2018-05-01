#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import pytest
from hypothesis import given
from hypothesis.strategies import text

from recval.normalization import normalize


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
