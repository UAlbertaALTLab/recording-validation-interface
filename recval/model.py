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

Do not use db directly; instead, use database.init_db() instead.
"""

import warnings
from datetime import datetime, time
from enum import Enum, auto
from hashlib import sha256
from os import fspath
from pathlib import Path

from flask import current_app, url_for  # type: ignore
from flask_security import (RoleMixin, SQLAlchemyUserDatastore,  # type: ignore
                            UserMixin)
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
    # history, timestamp, and an author.
    transcription_id = db.Column(db.Text, db.ForeignKey('versioned_string.id'),
                                 nullable=False)
    translation_id = db.Column(db.Text, db. ForeignKey('versioned_string.id'),
                               nullable=False)

    # Is this a word or a phrase?
    type = db.Column(db.Text, nullable=False)

    # Maintain the relationship to the transcription
    transcription_meta = db.relationship('VersionedString',
                                         foreign_keys=[transcription_id])
    translation_meta = db.relationship('VersionedString',
                                       foreign_keys=[translation_id])
    # One phrase may have one or more recordings.
    recordings = db.relationship('Recording')

    __mapper_args__ = {
        'polymorphic_on': type,
        # Sets 'type' to null, which is (intentionally) invalid!
        'polymorphic_identity': None
    }

    def __init__(self, *, transcription=None, translation=None,  **kwargs):
        # Create versioned transcription.
        if transcription or translation:
            super().__init__(
                transcription_meta=VersionedString.new(value=transcription),
                translation_meta=VersionedString.new(value=translation),
                **kwargs
            )
        else:
            super().__init__(**kwargs)

    @hybrid_property
    def transcription(self) -> str:
        value = self.transcription_meta.value
        assert value == normalize_utterance(value)
        return value

    @transcription.setter  # type: ignore
    def transcription(self, value: str) -> None:
        # TODO: set current author.
        previous = self.transcription_meta
        self.transcription_meta = previous.derive(value)

    @hybrid_property
    def translation(self) -> str:
        value = self.translation_meta.value
        assert value == normalize_utterance(value)
        return value

    @translation.setter  # type: ignore
    def translation(self, value: str) -> None:
        # TODO: set current author.
        previous = self.translation_meta
        self.translation_meta = previous.derive(value)

    @property
    def translation_history(self):
        return VersionedString.query.filter_by(
            provenance_id=self.translation_meta.provenance_id
        ).all()

    @property
    def transcription_history(self):
        return VersionedString.query.filter_by(
            provenance_id=self.transcription_meta.provenance_id
        ).all()

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
        assert bool(transcription) ^ bool(translation), (
            "Must search for one of transcription or translation; not both"
        )
        query = Phrase.query
        if transcription:
            query = query.\
                filter(VersionedString.id == cls.transcription_id)
        else:
            assert translation
            query = query.\
                filter(VersionedString.id == cls.translation_id)
        value = normalize_utterance(transcription or translation)
        return query.filter(VersionedString.value == value)

    @classmethod
    def search_by(cls, search_string: str):
        """
        Does a full-text search on both transcription and translation
        columns for the given word.
        """
        identity = cls.__mapper_args__['polymorphic_identity']

        # The idea of this query is to get a table of just all the versioned
        # strings that match the query, and then to join this table with the
        # phrase table.
        fts_query = text(f"""
           SELECT id FROM versioned_string, {VERSIONED_STRING_FTS}
            WHERE {VERSIONED_STRING_FTS} MATCH :query
              AND versioned_string.rowid = {VERSIONED_STRING_FTS}.docid
        """).\
            columns(id=db.String).\
            params(query=to_indexable_form(search_string)).\
            alias('fts_query')

        # Implict join with the search results to recover the phrases that
        # match EITHER the translation or the transcription.
        return cls.query.filter(
            (cls.translation_id == fts_query.c.id) |
            (cls.transcription_id == fts_query.c.id)
        )


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

    id = db.Column(DBSessionID, primary_key=True)
    date = db.Column(db.Date(), nullable=False)
    time_of_day = db.Column(db.Enum(TimeOfDay), nullable=True)
    location = db.Column(db.Enum(Location), nullable=True)
    subsession = db.Column(db.Integer(), nullable=True)

    recordings = db.relationship('Recording')

    @classmethod
    def from_session_id(cls, session_id: SessionID) -> 'RecordingSession':
        return cls(id=session_id,
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
    speaker = db.Column(db.Text, nullable=True)  # TODO: Versioned String?
    timestamp = db.Column(db.DateTime, nullable=False,
                          default=datetime.now)
    phrase_id = db.Column(db.Integer, db.ForeignKey('phrase.id'),
                          nullable=False)
    session_id = db.Column(DBSessionID, db.ForeignKey('session.id'),
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


class VersionedString(db.Model):  # type: ignore
    """
    A versioned string is is one with a history of what it used to be, and who
    said it.

    The actual value of a versioned string is ALWAYS normalized.
    """

    __tablename__ = 'versioned_string'

    # TODO: validator for this.
    id = db.Column(db.String, primary_key=True)
    value = db.Column(db.Text, nullable=False)

    # 'provenance' is simply the first string in the series.
    provenance_id = db.Column(db.String, db.ForeignKey('versioned_string.id'),
                              nullable=False)
    previous_id = db.Column(db.String, db.ForeignKey('versioned_string.id'),
                            nullable=True)
    author_id = db.Column(db.Integer(), db.ForeignKey('user.id'),
                          nullable=True)  # TODO: make this not nullable!
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # The very first string in the series.
    provenance = db.relationship('VersionedString',
                                 remote_side=[id],
                                 foreign_keys=[provenance_id],
                                 uselist=False)
    # The immediately last version of the string.
    previous = db.relationship('VersionedString',
                               remote_side=[id],
                               foreign_keys=[previous_id],
                               uselist=False)
    author = db.relationship('User', foreign_keys=[author_id])

    @validates('value')
    def validate_value(self, _key, utterance):
        value = normalize_utterance(utterance)
        assert len(value) > 0
        return value

    @validates('author_id')
    def validate_author_id(self, _key, author_id):
        if author_id is None:
            warnings.warn("Author should not be None, "
                          "and will be non-nullable in the future",
                          DeprecationWarning)
        return author_id

    @property
    def author_email(self) -> str:
        if self.author is None:
            return '<unknown>'
        return self.author.email

    @property
    def is_root(self) -> bool:
        return self.id == self.provenance_id

    def show(self) -> str:
        """
        Returns the VersionedString somewhat like a Git object:

        See: https://gist.github.com/masak/2415865

        TODO: test show() before and after provenance and ID are set.
        """
        def generate():
            if not self.is_root:
                assert self.previous_id is not None
                # Yield the provenance ONLY when this is a non-root commit.
                yield f"provenance {self.provenance_id}"
                yield f"previous {self.previous_id}"
            yield f"author {self.author_email}"
            yield f"date {self.timestamp.isoformat()}"
            yield ''
            yield self.value
        return '\n'.join(generate())

    def compute_sha256hash(self) -> str:
        """
        Compute a hash that can be used as a ID for this versioned string.
        """
        return sha256(self.show().encode('UTF-8')).hexdigest()

    def derive(self, value: str, author: 'User'=None) -> 'VersionedString':
        """
        Create a versioned string using this instance as its previous value.
        """
        child = type(self).new(value, author)
        child.previous_id = self.id
        child.provenance_id = self.provenance_id
        # Setting previous and provenance changed the hash, so recompute it.
        child.id = child.compute_sha256hash()
        assert child.id != child.provenance_id
        return child

    @classmethod
    def new(cls, value: str, author: 'User'=None) -> 'VersionedString':
        """
        Create a "root" versioned string.
        That is, it has no history, and its provenance is itself.
        """
        instance = cls(value=normalize_utterance(value),
                       previous_id=None,
                       timestamp=datetime.now(),
                       author=author)

        # This is the root version.
        instance.id = instance.compute_sha256hash()
        instance.provenance_id = instance.id
        return instance


VERSIONED_STRING_FTS = 'versioned_string_fts'

# Create a "content-less" full-text search table using SQLite3's FTS4 module.
# https://www.sqlite.org/fts3.html#_external_content_fts4_tables_
event.listen(
    VersionedString.__table__,
    'after_create',
    DDL(f'''
        CREATE VIRTUAL TABLE {VERSIONED_STRING_FTS}
        USING fts4(content={VersionedString.__tablename__}, value)
    ''').execute_if(dialect='sqlite')
)
# Make sure we drop the table too.
event.listen(
    VersionedString.__table__,
    'before_drop',
    DDL(f'''
        DROP TABLE {VERSIONED_STRING_FTS}
    ''').execute_if(dialect='sqlite')
)


@event.listens_for(VersionedString, 'after_insert')
def insert_into_fts_table(mapper, connection, target):
    """
    Automatically indexes terms for full-text search when they are inserted
    into the VersionedString table.
    """
    # In order to insert into a "contentless" FTS table, we MUST always insert
    # the rowid. However, we only know the hash of the versioned string we
    # just inserted; not the rowid. This insert statement lets the database
    # engine figure out the value from the rowid it created.
    connection.execute(
        f'''
           INSERT INTO {VERSIONED_STRING_FTS} (docid, value)
           SELECT rowid, ?
           FROM {VersionedString.__tablename__}
           WHERE id = ?
        ''', (to_indexable_form(target.value), target.id,)
    )


# Define models required for Flask-Security:
# https://pythonhosted.org/Flask-Security/quickstart.html
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):  # type: ignore
    """
    Specifies a user's roles. Possible roles:
     - site-admin
     - validator
     - instructor
     - <importer>

    Most of this code is boilerplate from:
    https://pythonhosted.org/Flask-Security/quickstart.html
    """
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):  # type: ignore
    """
    An author is allowed to create and update VersionedStrings.

    Most of this code is boilerplate from:
    https://pythonhosted.org/Flask-Security/quickstart.html
    """
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
