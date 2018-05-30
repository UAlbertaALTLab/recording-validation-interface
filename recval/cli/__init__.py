#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
Add user and database management commands to the Flask CLI.
"""

from recval.app import app

from .user import user_cli
from .db import db_cli
from .data import data_cli

# Export NOTHING. This is important!
__all__ = []  # type: ignore

app.cli.add_command(user_cli)
app.cli.add_command(db_cli)
app.cli.add_command(data_cli)
