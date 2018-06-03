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
Provides access to special user accounts. Users are loaded from the database,
*at import time*, so make sure to never from _<module> import <user> in the
global scope.

Usage:

    from recval.database.special_users import <user>
"""

import sys
import typing

from types import ModuleType


if typing.TYPE_CHECKING:
    from recval.model import User
    importer: User


class SpecialUsersModule(ModuleType):
    @property
    def importer(self) -> 'User':
        """
        The importer bot.
        """
        from recval.model import user_datastore
        from recval.database import _IMPORTER_EMAIL
        return user_datastore.find_user(email=_IMPORTER_EMAIL)


sys.modules[__name__] = SpecialUsersModule(__name__, __doc__)
