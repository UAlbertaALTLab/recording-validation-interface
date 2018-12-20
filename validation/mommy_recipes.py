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

See: https://model-mommy.readthedocs.io/en/latest/recipes.html
"""

import random
from model_mommy.recipe import Recipe
from validation.models import Speaker


def random_gender():
    """
    Returns a non-null gender for a speaker.

    For the recording search API, the speaker's gender MUST NOT be null.
    """
    code, _label = random.choice(Speaker.GENDER_CHOICES)
    return code

# Create a speaker instance.
speaker = Recipe(Speaker,
                 gender=random_gender())
