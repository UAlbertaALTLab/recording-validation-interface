#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
Defines rountines for creating the database.
"""


def init_db():
    """
    Initializes the database for the first time.
    """
    from recval.model import db
    db.create_all()
    return db
