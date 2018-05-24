#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import sys
import typing

from types import ModuleType

if typing.TYPE_CHECKING:
    from recval.model import User
    importer: User


class SpecialUsersModule(ModuleType):
    _IMPORTER_EMAIL = 'importer@localhost'

    @property
    def importer(self) -> 'User':
        from recval.model import user_datastore
        return user_datastore.find_user(email=self._IMPORTER_EMAIL)


sys.modules[__name__] = SpecialUsersModule(__name__)
