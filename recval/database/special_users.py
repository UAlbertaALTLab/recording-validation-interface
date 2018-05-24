#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

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
