#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

"""
TODO: Spend sprint 2 factoring things out of this file!
"""

from os import fspath
from pathlib import Path

from flask import (Flask, abort, redirect, render_template,  # type: ignore
                   request, send_from_directory, url_for)
from flask_security import (Security, SQLAlchemyUserDatastore,  # type: ignore
                            current_user, roles_required)
from sqlalchemy.orm import subqueryload  # type: ignore
from werkzeug.exceptions import NotFound  # type: ignore

from recval.model import Phrase, db, user_datastore

# Configure from default settings, then the file specifeied by the environment
# variable.
# See: http://flask.pocoo.org/docs/0.12/config/#configuring-from-files
app = Flask(__name__)
app.config.from_object('recval.default_settings')
app.config.from_envvar('RECVAL_SETTINGS')

# Setup SQLAlchemy
if app.config['SQLALCHEMY_DATABASE_URI'] == app.config['DEFAULT_DATABASE']:
    app.logger.warn('Using default database: %s', app.config['DEFAULT_DATABASE'])

# Setup SQLAlchemy and Flask-Security
db.init_app(app)
security = Security(app, user_datastore)


# Transcoded audio files.
AUDIO_MIME_TYPES = {
    '.m4a': 'audio/aac',
}


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


# TODO: require validator role
@app.route('/phrase/<int:phrase_id>', methods=['PATCH'])
@roles_required('validator')
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

    path = app.config['TRANSCODED_RECORDINGS_PATH']
    assert path.resolve().is_dir()
    return send_from_directory(fspath(path), filename,
                               mimetype=content_type)


@app.context_processor
def inject_user():
    return dict(user=current_user)
