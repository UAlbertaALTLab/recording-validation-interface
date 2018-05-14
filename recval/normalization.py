#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import re
import unicodedata


def normalize(utterance):
    r"""
    Normalizes utterances (translations, transcriptions, etc.)

    TODO: Should be idempotent. i.e.,

    assert normalize_utterance(s) == normalize_utterance(normalize_utterance(s))
    """
    return unicodedata.normalize('NFC', utterance.strip())


def to_indexable_form(text: str) -> str:
    """
    Converts text in SRO to a string to an indexable (searchable) form.
    """

    # TODO: definitely some unicode normalization going on here.

    return re.sub(r"(?<=[qwrtpsdfghjklzxcvbnm])'", "i", text)
