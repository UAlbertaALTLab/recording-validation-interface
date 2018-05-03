#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from datetime import datetime
from hashlib import sha256
from os import fspath
from pathlib import Path

from flask import current_app, url_for  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from sqlalchemy.orm import subqueryload, validates  # type: ignore

from recval.normalization import normalize as normalize_utterance


db = SQLAlchemy()
Model = db.Model


class Phrase(db.Model):  # type: ignore
    """
    A phrase is a sentence or a word.

    A phrase has a transcription and a translation.

    Note that translation and transcription MUST be NFC normalized!

    See: http://docs.sqlalchemy.org/en/latest/orm/inheritance.html#single-table-inheritance
    """
    __tablename__ = 'phrase'

    id = db.Column(db.Integer, primary_key=True)

    transcription_id = db.Column(db.Text, db.ForeignKey('versioned_string.id'),
                                 nullable=False)
    transcription_history = db.relationship('VersionedString')

    #transcription = db.Column(db.Text, nullable=False)  # TODO: convert to VersionedString
    translation = db.Column(db.Text, nullable=False)  # TODO: convert to VersionedString
    # Is this a word or a phrase?
    type = db.Column(db.Text, nullable=False)

    # One phrase may have one or more recordings.
    recordings = db.relationship('Recording')

    __mapper_args__ = {
        'polymorphic_on': type,
        # Sets 'type' to null, which is (intentionally) invalid!
        'polymorphic_identity': None
    }

    def __init__(self, *, transcription, **kwargs):
        # Create versioned
        super().__init__(
            transcription_history=VersionedString.new(value=transcription,
                                                      author_name='<unknown>'),
            **kwargs
        )

    @validates('translation')
    def validate_translation(self, _key, utterance):
        return self.validate_utterance(utterance)

    def update(self, field: str, value: str) -> 'Phrase':
        """
        Update the field: either a translation or a transcription.
        """
        assert field in ('translation', 'transcription')
        normalized_value = normalize_utterance(value)
        setattr(self, field, normalized_value)
        return self

    @staticmethod
    def validate_utterance(utterance):
        value = normalize_utterance(utterance)
        assert len(value) > 0
        return value


class Word(Phrase):
    """
    A single word, with a translation.

    Note that translation and transcription MUST be NFC normalized!
    """
    # A word may be contained within another sentence
    contained_within = db.Column(db.Integer, db.ForeignKey('phrase.id'),
                                 nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'word'
    }


# TODO: What about race-conditions?
# Keep it ACID. Use transactions.

class Sentence(Phrase):
    """
    An entire sentence, with a translation.

    May contain one or more words.

    Note that translation and transcription MUST be NFC normalized!
    """
    # NOTE: A sentence does not have any additional properties of its own.
    __mapper_args__ = {
        'polymorphic_identity': 'sentence'
    }


class Recording(db.Model):  # type: ignore
    """
    A recording of a phrase.

    This is CONTENT-ADDRESSED memory. The "fingerprint" is a SHA-256 sum of
    the raw recording file. The file itself is converted into ds

    """
    fingerprint = db.Column(db.Text, primary_key=True)
    speaker = db.Column(db.Text, nullable=True)  # TODO: Versioned String?
    timestamp = db.Column(db.DateTime, nullable=False,
                          default=datetime.utcnow)
    phrase_id = db.Column(db.Integer, db.ForeignKey('phrase.id'),
                          nullable=False)
    phrase = db.relationship('Phrase', back_populates='recordings')

    @classmethod
    def new(cls, phrase: Phrase, input_file: Path, speaker: str=None) -> 'Recording':
        """
        Create a new recording and transcode it for distribution.
        """
        assert input_file.exists()
        fingerprint = compute_fingerprint(input_file)
        transcode_to_aac(input_file, fingerprint)
        return cls(fingerprint=fingerprint,
                   phrase=phrase,
                   speaker=speaker)

    @property
    def aac_path(self) -> str:
        return url_for('send_audio', filename=f"{self.fingerprint}.mp4")


class VersionedString(db.Model):  # type: ignore
    """
    A versioned string is is one with a history of what it used to be, and who
    said it.

    The actual value of a versioned string is ALWAYS normalized.
    """

    __tablename__ = 'versioned_string'

    # TODO: validator for this.
    id = db.Column(db.String, primary_key=True)
    value = db.Column(db.Text, nullable=False)  # TODO: always normalize this!

    # 'provenance' is simply the id of the first string in the series.
    provenance = db.Column(db.String, db.ForeignKey('versioned_string.id'),
                           nullable=False)
    previous = db.Column(db.String, db.ForeignKey('versioned_string.id'),
                         nullable=True)

    # TODO: author as an entity
    author_name = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # TODO: create index on provenance to get full history

    @validates('value')
    def validate_value(self, _key, utterance):
        value = normalize_utterance(utterance)
        assert len(value) > 0
        return value

    def show(self) -> str:
        """
        Returns the VersionedString somewhat like a Git object:

        See: https://gist.github.com/masak/2415865

        TODO: test show() before and after provenance and ID are set.
        """
        def generate():
            if self.provenance and self.provenance != self.id:
                # Yield the provenance ONLY when this is a non-root commit.
                yield f"provenance {self.provenance}"
            if self.previous:
                yield f"previous {self.previous}"
            yield f"author {self.author_name}"
            yield f"date {self.timestamp:%Y-%m-%dT%H:%M:%S%z}"
            yield ''
            yield self.value
        return '\n'.join(generate())

    def compute_sha256hash(self) -> str:
        """
        Compute a hash that can be used as a ID for this versioned string.
        """
        return sha256(self.show().encode('UTF-8')).hexdigest()

    def derive(self, value: str, author_name: str) -> 'VersionedString':
        """
        Create a versioned string using this instance as its previous value.
        """
        # TODO: support for date.
        instance = type(self).new(value, author_name)
        instance.previous = self
        instance.provenance = self.provenance
        # Setting previous and provenance changed the hash,
        # so recompute it.
        instance.id = instance.compute_sha256hash()
        return instance

    @classmethod
    def new(cls, value: str, author_name: str) -> 'VersionedString':
        """
        Create a "root" versioned string.
        That is, it has no history, and its provenance is itself.
        """
        instance = cls(value=normalize_utterance(value),
                       timestamp=datetime.utcnow(),
                       author_name=author_name)

        # This is the root version.
        instance.id = instance.compute_sha256hash()
        instance.provenance = instance.id
        return instance


'''
I will implement this stuff in the next sprint, but I gotta get it out of
my mind first.

class Author(db.Model):
    """
    An author is allowed to create and update VersionedStrings.
    """
    email = db.Column(db.Text, primary_key=True)
'''


def compute_fingerprint(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of the given audio file path.
    """
    assert file_path.suffix == '.wav', f"Expected .wav file; got {file_path}"
    with open(file_path, 'rb') as f:
        return sha256(f.read()).hexdigest()


def transcode_to_aac(recording_path: Path, fingerprint: str) -> None:
    """
    Transcodes .wav files to .aac files.
    TODO: Factor this out!
    """
    from sh import ffmpeg  # type: ignore
    assert recording_path.exists(), f"Could not stat {recording_path}"
    assert len(fingerprint) == 64, f"expected fingerprint: {fingerprint!r}"

    # Determine where to read and write transcoded audio files.
    transcoded_recordings_path = Path(current_app.config['TRANSCODED_RECORDINGS_PATH']).resolve()
    assert transcoded_recordings_path.is_dir()

    out_filename = transcoded_recordings_path / f"{fingerprint}.mp4"
    if out_filename.exists():
        current_app.logger.info('File already transcoded. Skipping: %s', out_filename)
        return

    current_app.logger.info('Transcoding %s', recording_path)
    ffmpeg('-i', fspath(recording_path),
           '-nostdin',
           '-n',  # Do not overwrite existing files
           '-ac', 1,  # Mix to mono
           '-acodec', 'aac',  # Use the AAC codec
           out_filename)
