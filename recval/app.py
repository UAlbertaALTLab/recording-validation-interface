#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.


from flask import Flask, render_template  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore


app = Flask(__name__)
# XXX: temporary location for directory
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
# Diable object modication tracking -- unneeded, and silences a warning.
# See: http://flask-sqlalchemy.pocoo.org/2.3/config/#configuration-keys
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


class Recording(db.Model):  # type: ignore
    """
    Represents a recording of a phrase (word or sentence).
    """
    file_path = db.Column(db.Text(), primary_key=True)
    transcription = db.Column(db.Text())
    translation = db.Column(db.Text())
    speaker = db.Column(db.Text())


@app.route('/')
def list_all_words():
    return render_template(
        'index.html',
        recordings=Recording.query.all()
    )
