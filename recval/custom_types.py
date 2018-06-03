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
Custom SQLAlchemy types.
"""

from sqlalchemy.types import TypeDecorator, Unicode  # type: ignore

from recval.recording_session import SessionID


class DBSessionID(TypeDecorator):
    """
    A custom ID type that is essentially just the str() of a SessionID object.
    """
    impl = Unicode

    def process_bind_param(self, value: SessionID, _dialect) -> str:
        # "as_filename()" is a misnomer; it's actually a concise string
        # describing all of the identifying details of a session.
        return value.as_filename()

    def process_result_value(self, value: str, _dialect) -> SessionID:
        return SessionID.from_name(value)
