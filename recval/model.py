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
The data models for the validation app.

See database to initialize and create the database.

Do not use db directly; instead, use db.create_all() instead.
"""

import warnings
from datetime import datetime, time
from enum import Enum, auto
from hashlib import sha256
from os import fspath
from pathlib import Path

from flask import current_app, url_for  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from sqlalchemy import DDL, event  # type: ignore
from sqlalchemy.ext.hybrid import hybrid_property  # type: ignore
from sqlalchemy.sql.expression import text  # type: ignore
from sqlalchemy.orm import validates  # type: ignore

from recval.normalization import to_indexable_form, normalize as normalize_utterance
from recval.recording_session import SessionID, TimeOfDay, Location
from recval.custom_types import DBSessionID


db = SQLAlchemy()


class RecordingQuality(Enum):
    """
    Tag describing the quality of a recording.
    """
    clean = auto()
    unusable = auto()
    # TODO: add "exemplary" status?


class ElicitationOrigin(Enum):
    """
    How the particular phrase got it into the database in the first place.
    There are at least three sources:

     - word in the Maskwacîs dictionary.
     - word created using the Rapid Words methodology
       (https://www.sil.org/dictionaries-lexicography/rapid-word-collection-methodology)
     - word is in a sentence
    """
    maskwacîs = auto()
    rapid_words = auto()


class Phrase(db.Model):  # type: ignore
    """
    A phrase is a sentence or a word.

    A phrase has a transcription and a translation.

    Note that translation and transcription MUST be NFC normalized!

    See: http://docs.sqlalchemy.org/en/latest/orm/inheritance.html#single-table-inheritance
    """
    __tablename__ = 'phrase'

    id = db.Column(db.Integer, primary_key=True)

    # The transcription and translation are "versioned strings", with a
    # history, timestamp.
    transcription = db.Column(db.Text, nullable=False)
    translation = db.Column(db.Text, nullable=False)

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

    def __repr__(self):
        return f"<{type(self).__name__} {self.id} {self.transcription!r}>"

    @classmethod
    def query_by(cls, transcription=None, translation=None):
        """
        Returns a query that will search on the text value of transcription or
        translation.
        """
        raise NotImplementedError


class Word(Phrase):
    """
    A single word, with a translation.

    Note that translation and transcription MUST be NFC normalized!
    """

    # The elicitation origin of this term.
    origin = db.Column(db.Enum(ElicitationOrigin), nullable=True)

    # A sentence that contains this word.
    contained_within = db.Column(db.Integer, db.ForeignKey('phrase.id'),
                                 nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'word'
    }


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


class RecordingSession(db.Model):  # type: ignore
    """
    A session during which a number of recordings were made.

    THis is very similar to SessionID, but explicitly meant to be stored in
    the database.
    """
    __tablename__ = 'session'

    id = db.Column(db.Text, primary_key=True)
    date = db.Column(db.Date(), nullable=False)
    time_of_day = db.Column(db.Enum(TimeOfDay), nullable=True)
    location = db.Column(db.Enum(Location), nullable=True)
    subsession = db.Column(db.Integer(), nullable=True)

    recordings = db.relationship('Recording')

    @classmethod
    def from_session_id(cls, session_id: SessionID) -> 'RecordingSession':
        return cls(id=str(session_id),
                   date=session_id.date,
                   time_of_day=session_id.time_of_day,
                   location=session_id.location,
                   subsession=session_id.subsession)


class Recording(db.Model):  # type: ignore
    """
    A recording of a phrase.

    The id is a SHA-256 sum of either the session, or if session data is
    missing, the wav file itself.
    """
    id = db.Column(db.Text, primary_key=True)
    speaker = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False,
                          default=datetime.now)
    phrase_id = db.Column(db.Integer, db.ForeignKey('phrase.id'),
                          nullable=False)
    session_id = db.Column(db.Text, db.ForeignKey('session.id'),
                           nullable=False)

    quality = db.Column(db.Enum(RecordingQuality), nullable=True)

    phrase = db.relationship('Phrase', back_populates='recordings')
    session = db.relationship('RecordingSession', back_populates='recordings')

    @classmethod
    def new(cls, fingerprint: str, phrase: Phrase,
            session: RecordingSession,
            input_file: Path=None, speaker: str=None) -> 'Recording':
        """
        Create a new recording and transcode it for distribution.
        """
        # infer the timestamp from the session's date;
        # Because there's no reliable way to get the time, set it to
        # 00:00:00
        timestamp = datetime.combine(session.date, time())
        return cls(id=fingerprint, phrase=phrase, speaker=speaker,
                   session=session, timestamp=timestamp)
