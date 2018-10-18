#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Temporary dumping ground before I find a better place for whatever is in here.
"""

import os
import contextlib
from pathlib import Path

import click


def delete_audio(audio_dir: Path):
    click.secho(f'Deleting all *.m4a files in {audio_dir}', fg='red', bold=True)
    for audio_file in audio_dir.glob('*.m4a'):
        audio_file.unlink()


# Copied from: https://stackoverflow.com/a/24469659/6626414
@contextlib.contextmanager
def cd(path: Path):
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)
