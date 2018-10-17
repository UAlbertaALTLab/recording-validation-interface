#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Temporary dumping ground before I find a better place for whatever is in here.
"""

from pathlib import Path

import click


def delete_audio(audio_dir: Path):
    click.secho(f'Deleting all *.m4a files in {audio_dir}', fg='red', bold=True)
    for audio_file in audio_dir.glob('*.m4a'):
        audio_file.unlink()
