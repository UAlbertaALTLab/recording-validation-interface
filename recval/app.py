#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from datetime import datetime
from unicodedata import normalize

from flask import Flask, render_template  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore


app = Flask(__name__)
# XXX: temporary location for directory
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
# Diable object modication tracking -- unneeded, and silences a warning.
# See: http://flask-sqlalchemy.pocoo.org/2.3/config/#configuration-keys
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


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


class Word(db.Model):
    """
    A single word, with a translation.

    Note that translation and transcription MUST be NFC normalized!
    """
    id = db.Column(db.Integer, primary_key=True)
    transcription = db.Column(db.Text, nullable=False)
    translation = db.Column(db.Text, nullable=False)


class Sentence(db.Model):
    """
    An entire sentence, with a translation.

    May contain one or more words.

    Note that translation and transcription MUST be NFC normalized!
    """
    id = db.Column(db.Integer, primary_key=True)
    transcription = db.Column(db.Text, nullable=False)
    translation = db.Column(db.Text, nullable=False)
    # TODO: link with words


class Recording(db.Model):  # type: ignore
    """
    A recording of a phrase, with
    """
    file_path = db.Column(db.Text, primary_key=True)
    speaker = db.Column(db.Text, nullalble=True)


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
        head = ... # TimestampedString: nullable=False
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
        author = ... # TODO: author
        timestamp = db.Column(db.DateTime, nullable=False,
                              default=datetime.utcnow)
        previous = ... # TimestampedString nullable=True
        

    class Author(db.Model):
        """
        An author is allowed to create and update VersionedStrings.
        """
        email = db.Column(db.Text, primary_key=True)


@app.route('/')
def list_all_words():
    return render_template(
        'index.html',
        recordings=Recording.query.all()
    )
