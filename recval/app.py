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

from flask import (  # type: ignore
    Flask, abort, url_for, render_template, send_from_directory, redirect,
    request
)
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
    Normalizes utterances (translations, transcriptions, etc.)

    >>> normalize_utterance("  hello ")
    'hello'
    >>> normalize_utterance("pho\u031B\u0309 ")
    'phở'
    >>> normalize_utterance("   phơ\u0309 ")
    'phở'

    TODO: Should be idempotent. i.e.,

    assert normalize_utterance(s) == normalize_utterance(normalize_utterance(s))
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

    def update(self, field: str, value: str) -> 'Phrase':
        """
        Update the field: either a translation or a transcription.
        """
        assert field in ('translation', 'transcription')
        normalized_value = normalize_utterance(value)
        setattr(self, field, normalized_value)
        return self


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
    """
    id = db.Column(db.String, primary_key=True)  # TODO: validator for this.

    # id of the first commit.
    _provenance = db.Column(db.String, nullable=True)  # TODO: self-reference table
    _previous = db.Column(db.String, nullable=True)  # TODO: self-reference table
    # TODO: author as an entity
    author = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    value = db.Column(db.Text, nullable=False)  # TODO: always normalize this!

    # TODO: create index on provenance to get full history

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
            yield f"author {self.author}"
            yield f"date {self.timestamp:%Y-%m-%dT%H:%M:%S%z}"
            yield ''
            yield self.value
        return '\n'.join(generate())

    def compute_sha256hash(self) -> str:
        """
        Compute a hash that can be used as a ID for this versioned string.
        """
        return sha256(self.show().encode('UTF-8')).hexdigest()

    def derive(self, value: str, author: str) -> 'VersionedString':
        """
        Create a versioned string using this instance as its previous.
        """
        assert self.provenance is not None
        instance = type(self).new(value, author)
        instance.previous = self
        instance.provenance = self.provenance
        # Setting previous and provenance changed the hash,
        # so recompute it.
        instance.id = instance.compute_sha256hash()
        return instance

    @classmethod
    def new(cls, value: str, author: str) -> 'VersionedString':
        """
        Create a "root" versioned string.
        That is, it has no history, and its provenance is itself.
        """
        instance = cls(value=normalize_utterance(value),
                       timestamp=datetime.utcnow())

        # This is the root version.
        instance.id = instance.compute_sha256hash()
        instance.provenance = instance.id
        return instance


def _not_now():
    """
    I will implement this stuff in the next sprint, but I gotta get it out of
    my mind first.
    """

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

    out_filename = TRANSCODED_RECORDINGS_PATH / f"{fingerprint}.mp4"
    if out_filename.exists():
        app.logger.info('File already transcoded. Skipping: %s', out_filename)
        return

    app.logger.info('Transcoding %s', recording_path)
    ffmpeg('-i', fspath(recording_path),
           '-nostdin',
           '-n',  # Do not overwrite existing files
           '-ac', 1,  # Mix to mono
           '-acodec', 'aac',  # Use the AAC codec
           out_filename)


def compute_fingerprint(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of the given audio file path.
    """
    assert file_path.suffix == '.wav', f"Expected .wav file; got {file_path}"
    with open(file_path, 'rb') as f:
        return sha256(f.read()).hexdigest()


@app.route('/')
def index():
    """
    Redirects to the first page of phrases.
    """
    return redirect(url_for('list_phrases', page=1))


@app.route('/phrases/<int:page>/')
def list_phrases(page):
    """
    List SOME of the words, contrary to the name.
    """
    query = Phrase.query.options(subqueryload(Phrase.recordings))
    return render_template(
        'index.html',
        page=query.paginate(page=page)
    )


@app.route('/phrase/<int:phrase_id>', methods=['PATCH'])
def update_text(phrase_id):
    """
    Changes the text for a field of the given phrase.

    Takes in a JSON request body like this:

        {
            "field": "translation" | "transcription",
            "value": "<new contents for the field>",
        }
    """
    # Ensure the field exists first.
    body = request.get_json()
    field = body.get('field')
    value = body.get('value')
    # Reject requests with invalid arugm
    if not (field in ('translation', 'transcription') and isinstance(value, str)):
        abort(400)

    # TODO: Require a CSRF token, probably
    phrase = Phrase.query.filter(Phrase.id == phrase_id).one()

    # Actually update the translation or transcription.
    phrase.update(field, value)
    db.session.commit()
    return '', 204


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
