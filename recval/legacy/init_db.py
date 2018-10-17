#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Legacy recording importing stuff for Flask/SQLAlchemy
"""

from pathlib import Path

from recval.init_db import ImportRecording
from recval.init_db import initialize as _initialize
from recval.extract_phrases import RecordingInfo


def initialize(directory: Path) -> None:
    from recval.app import app
    return _initialize(
            directory,
            app.config['TRANSCODED_RECORDINGS_PATH'],
            app.config['REPOSITORY_ROOT'],
            FlaskSQLAlchemyRecordingImporter(),
    )


def FlaskSQLAlchemyRecordingImporter() -> ImportRecording:
    """
    Naming things is hard
    """

    from recval.database import init_db
    from recval.model import Phrase, VersionedString, Word, Sentence

    info2phrase = {}  # type: ignore
    db = init_db()

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

    def import_recording(info: RecordingInfo, rec_id: str, recording_path: Path) -> None:
        from recval.model import Recording, RecordingSession
        session = RecordingSession.query.filter_by(id=info.session).\
            one_or_none() or RecordingSession.from_session_id(info.session)
        phrase = make_phrase(info)
        # TODO: GENERATE SESSION ID!
        # TODO: I forgot what a "session" ID is! Like a recording session ID? Why!?
        recording = Recording.new(fingerprint=rec_id,
                                  phrase=phrase,
                                  input_file=recording_path,
                                  session=session,
                                  speaker=info.speaker)
        db.session.add(recording)
        db.session.commit()

    return import_recording
