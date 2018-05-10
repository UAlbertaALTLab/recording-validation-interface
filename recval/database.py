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
    from recval.model import db, user_datastore
    db.create_all()

    # Create roles.
    importer_role = user_datastore.create_role(
        name='<importer>',
        description='A bot that imports recordings and other data.'
    )

    # Create the special <importer> account.
    user_datastore.create_user(
        email='importer@localhost',
        password=None,
        active=False,
        confirmed_at=None,
        roles=[importer_role]
    )
    return db
