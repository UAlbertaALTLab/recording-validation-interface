#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
Initialize and update database
"""

import sys
from pathlib import Path

import click
from flask.cli import AppGroup, with_appcontext  # type: ignore

from recval.app import app


# Subcommand for database management.
db_cli = AppGroup('db', help=__doc__.strip())


@db_cli.command('init')
@with_appcontext
@click.argument('directory', envvar='RECVAL_SESSION_DIRECTORY', type=Path)
def init_db(directory: Path) -> None:
    """
    Creates the database from scratch.

    TODO: drastically fix this
    """

    import logging

    from recval.extract_phrases import RecordingExtractor, RecordingInfo
    from recval.model import (Phrase, Recording, Sentence, Word, VersionedString,
                              RecordingSession)
    from recval.database import init_db
    from recval.transcode_recording import transcode_to_aac
    from recval.recording_session import parse_metadata

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

    with open('metadata.csv') as metadata_file:
        metadata = parse_metadata(metadata_file)

    # Insert each thing found.
    # TODO: use click.progressbar()?
    logging.basicConfig(level=logging.INFO)
    ex = RecordingExtractor(metadata)
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

        session = RecordingSession.query.filter_by(id=info.session).\
            one_or_none() or RecordingSession.from_session_id(info.session)
        phrase = make_phrase(info)
        # TODO: GENERATE SESSION ID!
        recording = Recording.new(fingerprint=rec_id,
                                  phrase=phrase,
                                  input_file=recording_path,
                                  session=session,
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
