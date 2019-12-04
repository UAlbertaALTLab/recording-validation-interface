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
Old CLI commands that should be ported to the new framework.
"""

import click
from pathlib import Path


def delete_audio(audio_dir: Path) -> None:
    """
    Deletes all of the audio in the given audio directory.

    Good for nuking the development environment and starting from scratch.
    """
    click.secho(f"Deleting all *.m4a files in {audio_dir}", fg="red", bold=True)
    for audio_file in audio_dir.glob("*.m4a"):
        audio_file.unlink()
