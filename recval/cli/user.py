#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
List, create, and update user accounts.
"""

import sys

import click
from flask.cli import AppGroup, with_appcontext  # type: ignore

user_cli = AppGroup('user', help=__doc__.strip())


@user_cli.command('create')
@with_appcontext
@click.argument('email')
@click.option('--community/--no-community', default=True)
@click.option('--validator/--no-validator', default=False)
def create_user(email: str, community: bool, validator: bool) -> None:
    """
    Create a new user with the given email.

    The user will have the 'community' role by default; pass
    `--validator` to add them to the "validator" role as well.
    """
    from getpass import getpass
    from datetime import datetime

    from flask_security.utils import hash_password  # type: ignore

    from recval.model import db, user_datastore

    if user_datastore.find_user(email=email):
        print("There is already a user whose email is", email + "!")
        sys.exit(1)

    print("Creating user with email", email)
    password = getpass(f'Enter a new password for {email}: ')
    password_verify = getpass('Re-type password: ')
    if password != password_verify:
        print("Passwords did not match")
        sys.exit(1)

    roles = []
    if community:
        roles.append('community')
    if validator:
        roles.append('validator')

    print(f"Creating user:")
    print("  Email:", email)
    print("  Password:", "*" * 8)
    print("  Roles:", ', '.join(sorted(roles)))
    if not click.confirm("Is this okay?"):
        print("Will NOT create user.")
        sys.exit(1)

    new_user = user_datastore.create_user(
        email=email,
        password=hash_password(password),
        active=True,
        confirmed_at=datetime.utcnow(),
        roles=roles
    )
    db.session.commit()

    # Make sure we stored them!
    stored_user = user_datastore.find_user(email=email)
    assert stored_user is not None
    assert all(stored_user.has_role(r) for r in roles)


@user_cli.command('list')
@with_appcontext
def list_users():
    """
    List all users and their roles.
    """
    from recval.model import User

    template = "{email:24} | {roles:24}"
    print(template.format(email='Email', roles='Roles'))
    for user in User.query.all():
        print(template.format(
            email=user.email,
            roles=','.join(sorted(role.name for role in user.roles))
        ))


@user_cli.command('assign-role')
@with_appcontext
@click.argument('role')
@click.argument('emails', nargs=-1)
def assign_role(role, emails):
    """
    Add roles to one or more users.
    """

    from recval.app import user_datastore, db
    role_obj = user_datastore.find_role(role)
    if not role_obj:
        click.secho(f"No such role exists: {role}",
                    fg="red", err=True)
        sys.exit(1)

    for email in emails:
        user = user_datastore.get_user(email)
        if not user:
            click.secho(f"No such user: {email}",
                        fg="red", err=True)
            sys.exit(1)
        user_datastore.add_role_to_user(user, role_obj)
    db.session.commit()


@user_cli.command('remove-role')
@with_appcontext
@click.argument('role')
@click.argument('emails', nargs=-1)
def remove_role(role, emails):
    """
    Remove specified role from one or more users.
    """

    from recval.app import user_datastore, db
    role_obj = user_datastore.find_role(role)
    if not role_obj:
        click.secho(f"No such role exists: {role}",
                    fg="red", err=True)
        sys.exit(1)

    for email in emails:
        user = user_datastore.get_user(email)
        if not user:
            click.secho(f"No such user: {email}",
                        fg="red", err=True)
            sys.exit(1)
        user_datastore.remove_role_from_user(user, role_obj)
    db.session.commit()
