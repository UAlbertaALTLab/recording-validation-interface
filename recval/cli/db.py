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
Initialize and update database
"""

import sys
from pathlib import Path

import click
from flask.cli import AppGroup, with_appcontext  # type: ignore

from recval.app import app
from recval.utils import delete_audio


# Subcommand for database management.
db_cli = AppGroup('db', help=__doc__.strip())


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

    delete_audio(audio_dir)
