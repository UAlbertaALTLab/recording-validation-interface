#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
TODO: Spend sprint 2 factoring things out of this file!
"""

from os import fspath
from datetime import datetime
from unicodedata import normalize
from pathlib import Path
from hashlib import sha256

from flask import Flask, url_for, render_template, send_from_directory  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from sqlalchemy.orm import subqueryload  # type: ignore
from werkzeug.exceptions import NotFound  # type: ignore

# Configure from default settings, then the file specifeied by the environment
# variable.
# See: http://flask.pocoo.org/docs/0.12/config/#configuring-from-files
app = Flask(__name__)
app.config.from_object('recval.default_settings')
app.config.from_envvar('RECVAL_SETTINGS')

# Setup SQLAlchemy
if app.config['SQLALCHEMY_DATABASE_URI'] == app.config['DEFAULT_DATABASE']:
    app.logger.warn('Using default database: %s', app.config['DEFAULT_DATABASE'])
db = SQLAlchemy(app)

# Determine where to read and write transcoded audio files.
TRANSCODED_RECORDINGS_PATH = Path(app.config['TRANSCODED_RECORDINGS_PATH']).resolve()
assert TRANSCODED_RECORDINGS_PATH.is_dir()

# Transcoded audio files.
AUDIO_MIME_TYPES = {
    '.mp4': 'audio/aac',
}


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
        return url_for('send_audio', filename=f"{self.fingerprint}.mp4")


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
    assert recording_path.exists(), f"Could not stat {recording_path}"
    assert len(fingerprint) == 64, f"Unexpced fingerprint: {fingerprint!r}"

    app.logger.info('Transcoding %s', recording_path)
    ffmpeg('-i', fspath(recording_path),
           '-ac', 1,  # Mix to mono
           '-acodec', 'aac',  # Use the AAC codec
           TRANSCODED_RECORDINGS_PATH / f"{fingerprint}.mp4")


def compute_fingerprint(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of the given audio file path.
    """
    assert file_path.suffix == '.wav', f"Expected .wav file; got {file_path}"
    with open(file_path, 'rb') as f:
        return sha256(f.read()).hexdigest()


@app.route('/')
def list_phrases():
    """
    List SOME of the words, contrary to the name.
    """
    query = Phrase.query.options(subqueryload(Phrase.recordings))
    return render_template(
        'index.html',
        page=query.paginate()
    )


@app.route('/static/audio/<filename>')
def send_audio(filename):
    """
    Send a previously transcoded audio file.

    See compute_fingerprint() and transcode_to_aac()
    """
    # Fail if we don't recognize the file extension.
    try:
        content_type = AUDIO_MIME_TYPES[Path(filename).suffix]
    except KeyError:
        raise NotFound

    # TODO: load transcoded path from Flask config
    return send_from_directory(fspath(TRANSCODED_RECORDINGS_PATH),
                               filename, mimetype=content_type)
