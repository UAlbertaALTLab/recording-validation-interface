#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
Defines rountines for creating the database.
"""

from werkzeug.local import LocalProxy

# The default email addres of the importer user. It should not really exist.
_IMPORTER_EMAIL = 'importer@localhost'


# A proxy for the importer -- a bot with the <importer> role.
@LocalProxy
def importer():
    from recval.model import user_datastore
    return user_datastore.find_user(email=_IMPORTER_EMAIL)


def init_db():
    """
    Initializes the database for the first time.
    """
    from recval.model import db, user_datastore
    db.create_all()

    # Create roles.
    importer_role = user_datastore.find_or_create_role(
        name='<importer>',
        description='A bot that imports recordings and other data.'
    )
    user_datastore.find_or_create_role(
        name='validator',
        description='A user that can change transcriptions and translations'
    )
    user_datastore.find_or_create_role(
        name='community',
        description='A community member can list phrases and hear recordings',
    )

    # Create the special <importer> account.
    user_datastore.create_user(
        email=_IMPORTER_EMAIL,
        password=None,
        active=False,
        confirmed_at=None,
        roles=[importer_role]
    )
    return db
