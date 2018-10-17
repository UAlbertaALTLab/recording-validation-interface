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
Defines rountines for creating the database.
"""

import typing

from recval.model import User


def init_db():
    """
    Initializes the database for the first time.
    """
    from recval.model import db, user_datastore
    db.create_all()

    # Create roles.
    user_datastore.find_or_create_role(
        name='validator',
        description='A user that can change transcriptions and translations'
    )
    user_datastore.find_or_create_role(
        name='community',
        description='A community member can list phrases and hear recordings',
    )

    return db
