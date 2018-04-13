#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.


from flask import Flask, render_template  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore

from unicodedata import normalize

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


# TODO: versioned string


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
    Represents a recording of a phrase (word or sentence).
    """
    file_path = db.Column(db.Text, primary_key=True)
    speaker = db.Column(db.Text)


@app.route('/')
def list_all_words():
    return render_template(
        'index.html',
        recordings=Recording.query.all()
    )
