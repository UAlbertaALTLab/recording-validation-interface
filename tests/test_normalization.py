#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from recval.normalization import normalize


def test_basic():
    assert 'hello' == normalize("  hello ")


def test_nfc():
    assert normalize("   phơ\u0309 ") == normalize("pho\u031B\u0309 ")
