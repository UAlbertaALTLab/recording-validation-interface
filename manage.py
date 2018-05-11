#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Script to manage user accounts.
"""

import argparse
import sys
from datetime import datetime
from getpass import getpass

from flask_security.utils import hash_password  # type: ignore


def create(args):
    """
    Create a new user.
    """
    from recval.app import app, user_datastore, db

    email = args.email

    with app.app_context():
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
    confirmation = input("Is this okay? (y/n) ")
    if not confirmation.lower().startswith('y'):
        print("Will NOT create user.")
        sys.exit(1)

    with app.app_context():
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


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

parser_create = subparsers.add_parser('create')
parser_create.add_argument('email')
parser_create.add_argument('--validator', action='store_true', default=True)
parser_create.set_defaults(func=create)


if __name__ == '__main__':
    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.error('must specify a subcommand')
    args.func(args)
