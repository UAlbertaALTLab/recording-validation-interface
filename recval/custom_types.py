#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

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
