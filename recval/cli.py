#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import sys
from typing import List
from pathlib import Path

import click
from flask import Flask  # type: ignore
from flask.cli import AppGroup, with_appcontext  # type: ignore

from recval.app import app


__all__: List[str] = []

# Create a group for user management commands
user_cli = AppGroup('user', help='List, create, and update users accounts')
db_cli = AppGroup('db', help='Initialize and update database')


@user_cli.command('create')
@with_appcontext
@click.argument('email')
@click.option('--community/--no-community', default=True)
@click.option('--validator/--no-validator', default=False)
def create_user(email, community, validator):
    """
    Create a new user with the given email.

    The user will have the 'community' role by default; pass
    `--validator` to add them to the "validator" role as well.
    """
    from getpass import getpass
    from datetime import datetime

    from flask_security.utils import hash_password  # type: ignore

    from recval.app import user_datastore, db

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


@db_cli.command('init')
@with_appcontext
@click.argument('directory', type=Path)
def init_db(directory: Path) -> None:
    """
    Creates the database from scratch.
    """

    import logging

    from recval.extract_phrases import RecordingExtractor, RecordingInfo
    from recval.model import Phrase, Recording, Sentence, Word, VersionedString
    from recval.database import init_db
    from recval.transcode_recording import transcode_to_aac

    # TODO: have a default place to look for sessions?

    info2phrase = {}  # type: ignore

    dest = Path(app.config['TRANSCODED_RECORDINGS_PATH'])

    assert directory.resolve().is_dir()
    assert dest.resolve().is_dir()

    def make_phrase(info: RecordingInfo) -> Phrase:
        """
        Tries to fetch an existing phrase from the database, or else creates a
        new one.
        """

        key = info.type, info.transcription

        if key in info2phrase:
            # Look up the phrase.
            phrase_id = info2phrase[key]
            return Phrase.query.filter_by(id=phrase_id).one()

        # Otherwise, create a new phrase.
        transcription = fetch_versioned_string(info.transcription)
        translation = fetch_versioned_string(info.translation)
        if info.type == 'word':
            p = Word(transcription_meta=transcription,
                     translation_meta=translation)
        elif info.type == 'sentence':
            p = Sentence(transcription_meta=transcription,
                         translation_meta=translation)
        else:
            raise Exception(f"Unexpected phrase type: {info.type!r}")
        assert p.id is None
        db.session.add(p)
        db.session.commit()
        assert p.id is not None
        info2phrase[key] = p.id
        return p

    def fetch_versioned_string(value: str) -> VersionedString:
        """
        Get a versioned string.
        """
        from recval.database.special_users import importer
        res = VersionedString.query.filter_by(value=value).all()
        assert len(res) in (0, 1)
        if res:
            return res[0]
        v = VersionedString.new(value=value, author=importer)
        return v

    # Create the schema.
    db = init_db()

    # Insert each thing found.
    # TODO: use click.progressbar()?
    logging.basicConfig(level=logging.INFO)
    ex = RecordingExtractor()
    for info, audio in ex.scan(root_directory=directory):
        rec_id = info.compute_sha256hash()
        recording_path = dest / f"{rec_id}.m4a"
        if not recording_path.exists():
            # https://www.ffmpeg.org/doxygen/3.2/group__metadata__api.html
            transcode_to_aac(audio, recording_path, tags=dict(
                title=info.transcription,
                performer=info.speaker,
                album=info.session,
                language="crk",
                creation_time=f"{info.session.date:%Y-%m-%d}",
                year=info.session.year
            ))
            assert recording_path.exists()

        phrase = make_phrase(info)
        recording = Recording.new(fingerprint=rec_id,
                                  phrase=phrase,
                                  input_file=recording_path,
                                  speaker=info.speaker)
        db.session.add(recording)
        db.session.commit()


@db_cli.command('destroy')
@with_appcontext
def destroy_db() -> None:
    """
    Deletes the database and all transcoded audio files.
    Intended for development environments only!
    """

    # Do nothing if not interactive.
    if app.config['ENV'] != 'development':
        click.echo("This option is only applicable in development mode!",
                   err=True)
        sys.exit(1)

    db_file = Path('/tmp/recval-temporary.db')
    audio_dir = Path(app.config['TRANSCODED_RECORDINGS_PATH'])

    click.confirm(
        f"Are you sure want to delete the database ({db_file}) "
        f" and all transcoded recordings in {audio_dir}?",
        abort=True
    )
    try:
        click.secho(f'Deleting {db_file}', fg='red', bold=True)
        db_file.unlink()
    except FileNotFoundError:
        pass

    click.secho(f'Deleting all *.m4a files in {audio_dir}',
                fg='red', bold=True)
    for audio_file in audio_dir.glob('*.m4a'):
        audio_file.unlink()


app.cli.add_command(user_cli)  # type: ignore
app.cli.add_command(db_cli)  # type: ignore
