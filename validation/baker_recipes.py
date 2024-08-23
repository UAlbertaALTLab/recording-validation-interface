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


"""
Modee Mommy recipes, for use in tests of the Validation app.

See: https://model-baker.readthedocs.io/en/latest/recipes.html
"""

import random

from model_bakery.recipe import Recipe, foreign_key

from validation.models import Phrase, Recording, Speaker, LanguageVariant

# What's the shortest a transcription can be (characters)?
MIN_TRANSCRIPTION_LENGTH = 2
# What's the longest a transcription can be (characters)?
MAX_TRANSCRIPTION_LENGTH = 64

# What's the longest a recording can be, in milliseconds?
MAX_RECORDING_LENGTH = 2**31 - 1


def random_gender():
    """
    Returns a non-null gender for a speaker.

    For the recording search API, the speaker's gender MUST NOT be null.
    """
    code, _label = random.choice(Speaker.GENDER_CHOICES)
    return code


def random_timestamp():
    """
    Create a valid timestamp for when a recording starts.
    """
    return random.randint(0, MAX_RECORDING_LENGTH)


def random_transcription():
    """
    Create a random phrase out of the Cree alphabet.
    """
    alphabet = "ptkcsmnywrlêioaîôâ"
    quantity = random.randint(MIN_TRANSCRIPTION_LENGTH, MAX_TRANSCRIPTION_LENGTH)
    return "".join(random.choice(alphabet) for _ in range(quantity))


# ################################ Recipes ################################ #

# A Speaker with a non-null gender.
speaker = Recipe(Speaker, gender=random_gender())


# A phrase with an SRO-ish transcription.
phrase = Recipe(Phrase, transcription=random_transcription)

recording = Recipe(
    Recording,
    timestamp=random_timestamp,
    phrase=foreign_key(phrase),
    speaker=foreign_key(speaker),
)

language = Recipe(LanguageVariant, name="Maskwacîs", code="maskwacis")
