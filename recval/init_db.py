#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Temporary place for database creation glue code.
"""
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from recval.extract_phrases import RecordingExtractor, RecordingInfo
from recval.transcode_recording import transcode_to_aac
from recval.recording_session import parse_metadata


def initialize(directory: Path) -> None:
    from recval.app import app
    return _initialize(
            directory,
            app.config['TRANSCODED_RECORDINGS_PATH'],
            app.config['REPOSITORY_ROOT']
    )


class RecordingImporter:
    """
    Naming things is hard
    """

    def __init__(self) -> None:
        from recval.database import init_db
        self.info2phrase = {}  # type: ignore
        self.db = init_db()

    if TYPE_CHECKING:
        from recval.model import Phrase, VersionedString

    def make_phrase(self, info: RecordingInfo) -> Phrase:
        """
        Tries to fetch an existing phrase from the database, or else creates a
        new one.
        """
        from recval.model import Phrase, Word, Sentence

        key = info.type, info.transcription

        if key in self.info2phrase:
            # Look up the phrase.
            phrase_id = self.info2phrase[key]
            return Phrase.query.filter_by(id=phrase_id).one()

        # Otherwise, create a new phrase.
        transcription = self.fetch_versioned_string(info.transcription)
        translation = self.fetch_versioned_string(info.translation)
        if info.type == 'word':
            p = Word(transcription_meta=transcription,
                     translation_meta=translation)
        elif info.type == 'sentence':
            p = Sentence(transcription_meta=transcription,
                         translation_meta=translation)
        else:
            raise Exception(f"Unexpected phrase type: {info.type!r}")
        assert p.id is None
        self.db.session.add(p)
        self.db.session.commit()
        assert p.id is not None
        self.info2phrase[key] = p.id
        return p

    def fetch_versioned_string(self, value: str) -> VersionedString:
        """
        Get a versioned string.
        """
        from recval.model import Phrase, VersionedString
        from recval.database.special_users import importer
        res = VersionedString.query.filter_by(value=value).all()
        assert len(res) in (0, 1)
        if res:
            return res[0]
        v = VersionedString.new(value=value, author=importer)
        return v

    def import_recording(self, info: RecordingInfo, rec_id: str, recording_path: Path) -> None:
        from recval.model import Recording, RecordingSession
        session = RecordingSession.query.filter_by(id=info.session).\
            one_or_none() or RecordingSession.from_session_id(info.session)
        phrase = self.make_phrase(info)
        # TODO: GENERATE SESSION ID!
        recording = Recording.new(fingerprint=rec_id,
                                  phrase=phrase,
                                  input_file=recording_path,
                                  session=session,
                                  speaker=info.speaker)
        self.db.session.add(recording)
        self.db.session.commit()


def _initialize(
        directory: Path,
        transcoded_recordings_path: str,
        repository_root: Path,
        ) -> None:
    """
    Creates the database from scratch.

    TODO: drastically fix this
    """

    from recval.model import (Phrase, Recording, Sentence, Word, VersionedString,
                              RecordingSession)

    dest = Path(transcoded_recordings_path)
    metadata_filename = repository_root / 'etc' / 'metadata.csv'

    assert directory.resolve().is_dir()
    assert dest.resolve().is_dir()
    assert metadata_filename.resolve().is_file()

    importer = RecordingImporter()

    with open(metadata_filename) as metadata_csv:
        metadata = parse_metadata(metadata_csv)

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
        importer.import_recording(info, rec_id, recording_path)
