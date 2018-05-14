#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import re
import unicodedata


def normalize(utterance):
    r"""
    Normalizes utterances (translations, transcriptions, etc.)
    """
    return unicodedata.normalize('NFC', utterance.strip())


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
