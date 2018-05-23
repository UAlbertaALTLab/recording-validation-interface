#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import sys
from getpass import getpass
from typing import List

import click
from flask import Flask  # type: ignore
from flask.cli import AppGroup, with_appcontext  # type: ignore

from recval.app import app


__all__: List[str] = []

# Create a group for user management commands
user_cli = AppGroup('user', help='List, create, and update users accounts')


@user_cli.command('create')
@with_appcontext
@click.argument('email')
def create(email):
    """
    Create a new user with the given email.
    """
    from recval.app import user_datastore, db
    from flask_security.utils import hash_password  # type: ignore
    from datetime import datetime

    if user_datastore.find_user(email=email):
        print("There is already a user whose email is", email + "!")
        sys.exit(1)

    print("Creating user with email", email)
    password = getpass(f'Enter a new password for {email}: ')
    password_verify = getpass('Re-type password: ')
    if password != password_verify:
        print("Passwords did not match")
        sys.exit(1)

    print("Creating validator:")
    print("  Email:", email)
    print("  Password:", "*" * 8)
    if not click.confirm("Is this okay?"):
        print("Will NOT create user.")
        sys.exit(1)

    new_user = user_datastore.create_user(
        email=email,
        password=hash_password(password),
        active=True,
        confirmed_at=datetime.utcnow(),
        roles=['validator']
    )
    db.session.commit()

    # Make sure we stored them!
    stored_user = user_datastore.find_user(email=email)
    assert stored_user is not None
    assert stored_user.has_role('validator')


app.cli.add_command(user_cli)
