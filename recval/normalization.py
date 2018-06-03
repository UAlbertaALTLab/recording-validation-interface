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
