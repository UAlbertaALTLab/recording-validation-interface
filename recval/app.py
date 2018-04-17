#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from os import fspath
from datetime import datetime
from unicodedata import normalize
from pathlib import Path
from hashlib import sha256

from flask import Flask, render_template, send_from_directory  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from sqlalchemy.orm import subqueryload  # type: ignore


app = Flask(__name__)
# TODO: allow configuration for this.
# XXX: temporary location for directory
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
# Diable object modication tracking -- unneeded, and silences a warning.
# See: http://flask-sqlalchemy.pocoo.org/2.3/config/#configuration-keys
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

here = Path('.').parent
TRANSCODED_RECORDINGS_PATH = here / 'static' / 'audio'


def normalize_utterance(utterance):
    r"""
    >>> normalize_utterance("  hello ")
    'hello'
    >>> normalize_utterance("pho\u031B\u0309 ")
    'phở'
    >>> normalize_utterance("   phơ\u0309 ")
    'phở'
    """
    return normalize('NFC', utterance.strip())


class Phrase(db.Model):  # type: ignore
    """
    A phrase is a sentence or a word.

    A phrase has a transcription and a translation.

    Note that translation and transcription MUST be NFC normalized!

    See: http://docs.sqlalchemy.org/en/latest/orm/inheritance.html#single-table-inheritance
    """
    __tablename__ = 'phrase'

    id = db.Column(db.Integer, primary_key=True)
    transcription = db.Column(db.Text, nullable=False)  # TODO: convert to VersionedString
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
    # TODO: fingerprint the source wave file, convert to Vorbis audio/web (.weba)
    fingerprint = db.Column(db.Text, primary_key=True)
    speaker = db.Column(db.Text, nullable=True)  # TODO: Versioned String?
    timestamp = db.Column(db.DateTime, nullable=False,
                          default=datetime.utcnow)
    phrase_id = db.Column(db.Integer, db.ForeignKey('phrase.id'),
                          nullable=False)
    phrase = db.relationship('Phrase', back_populates='recordings')
    # TODO: have an href webm link

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
        return fspath(TRANSCODED_RECORDINGS_PATH / (self.fingerprint + '.mp4'))


def _not_now():
    """
    I will implement this stuff in the next sprint, but I gotta get it out of
    my mind first.
    """

    class VersionedString(db.Model):
        """
        A versioned string is is one with a history of what it was, and who
        said it.

        This is essentially represented as a linked list of TimestampedString
        rows.
        """
        head = ...  # TimestampedString: nullable=False
        # TODO: convenience methods to access value, author, timestamp, of
        # most recent.

    class TimestampedString(db.Model):
        """
        A string with the author, and when the author wrote it. Can reference
        a previous TimestampedString which implies that this string is an
        revision of that string.

        Essentially a linked list node.
        """
        value = str  # TODO: always normalize this!
        author = ...  # TODO: author
        timestamp = db.Column(db.DateTime, nullable=False,
                              default=datetime.utcnow)
        previous = ...  # TimestampedString nullable=True

    class Author(db.Model):
        """
        An author is allowed to create and update VersionedStrings.
        """
        email = db.Column(db.Text, primary_key=True)


def transcode_to_aac(recording_path: Path, fingerprint: str) -> None:
    """
    Transcodes .wav files to .aac files.
    TODO: Factor this out!
    """
    from sh import ffmpeg  # type: ignore
    assert recording_path.exists(), f"got {recording_path}"
    assert len(fingerprint) == 64, f"got {fingerprint!r}"

    app.logger.info('Transcoding %s', recording_path)
    ffmpeg('-i', fspath(recording_path),
           '-ac', 1,  # Mix to mono
           '-acodec', 'aac',  # Use the AAC codec
           TRANSCODED_RECORDINGS_PATH / f"{fingerprint}.mp4")


def compute_fingerprint(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of the given audio file path.
    """
    assert file_path.suffix == '.wav', f"got {file_path}"
    with open(file_path, 'rb') as f:
        return sha256(f.read()).hexdigest()


@app.route('/')
def list_all_words():
    """
    """
    query = Phrase.query.options(subqueryload(Phrase.recordings))
    return render_template(
        'index.html',
        phrases=query.all()
    )


@app.route('/static/audio/<path>')
def send_audio(path):
    """
    Send a previously transcoded audio file.

    See compute_fingerprint() and transcode_to_aac()
    """
    # TODO: load transcoded path from Flask config
    content_type = mimetypes = {
        '.mp4': 'audio/aac',
        '.wav': 'audio/wave',
    }.get(path[-4], None)

    return send_from_directory(fspath(TRANSCODED_RECORDINGS_PATH.resolve()),
                               path,
                               mimetype=content_type)
