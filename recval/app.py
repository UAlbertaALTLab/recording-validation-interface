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

from os import fspath
from pathlib import Path

from flask import (Flask, abort, redirect, render_template,  # type: ignore
                   request, send_from_directory, url_for)
from flask_security import roles_required  # type: ignore
from sqlalchemy.orm import subqueryload  # type: ignore
from werkzeug.exceptions import NotFound  # type: ignore

from recval.model import Phrase, Recording, db
from recval.model import ElicitationOrigin, RecordingQuality

# Configure from default settings, then the file specifeied by the environment
# variable.
# See: http://flask.pocoo.org/docs/0.12/config/#configuring-from-files
app = Flask(__name__)
app.config.from_object('recval.default_settings')
app.config.from_envvar('RECVAL_SETTINGS')

# Setup SQLAlchemy
if app.config['SQLALCHEMY_DATABASE_URI'] == app.config['DEFAULT_DATABASE']:
    app.logger.warning('Using default database: %s', app.config['DEFAULT_DATABASE'])

# Setup SQLAlchemy and Flask-Security
db.init_app(app)
from .cli import *  # noqa


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
    Paginate all of the phrases in the database.
    """
    query = Phrase.query.options(subqueryload(Phrase.recordings))
    return render_template(
        'list_phrases.html',
        page=query.paginate(page=page)
    )


@app.route('/phrases/')
def search_phrases():
    """
    Searches for phrases.

    Query parameters:
        q=  fuzzy-match an entire word
    """
    query_text = request.args.get('q')
    if query_text is None:
        abort(400)
    query = Phrase.search_by(query_text)
    # page = int(request.args.get('page', 1))
    return render_template(
        'search.html',
        page=query.paginate(),
        search_term=query_text
    )


@app.route('/phrase/<int:phrase_id>')
@roles_required('validator')
def edit_phrase(phrase_id):
    phrase = Phrase.query.filter_by(id=phrase_id).one()
    return render_template('edit_phrase.html',
                           phrase=phrase,
                           origins=ElicitationOrigin,
                           qualities=RecordingQuality)


@app.route('/phrase/<int:phrase_id>', methods=['PATCH'])
@roles_required('validator')
def update_text(phrase_id):
    """
    Changes the text for a field of the given phrase.

    Takes in a JSON request body like this:

        {
            "value": "<new contents for the field>",
        }
    """

    payload = request.get_json()
    phrase = Phrase.query.filter_by(id=phrase_id).one()
    valid_fields = 'transcription', 'translation', 'origin'

    # Reject any requests that contain extraneous fields.
    if any(f not in valid_fields for f in payload):
        abort(400)

    # Set the translation and transcription first.
    for field in 'translation', 'transcription':
        if field in payload:
            value = payload[field]
            if not isinstance(value, str) or len(value) < 1:
                abort(400)
            setattr(phrase, field, value)

    # Set the origin.
    if 'origin' in payload:
        valid_origins = (o.name for o in ElicitationOrigin)
        value = payload['origin']
        if value not in (None, *valid_origins):
            abort(400)
        phrase.origin = value

    db.session.commit()
    return '', 204


@app.route('/recording/<recording_id>', methods=['PATCH'])
@roles_required('validator')
def update_recording(recording_id):
    """
    Changes the assigned quality of the recording.

    {
        "quality": "clean" | "unusable" | null
    }
    """

    levels = [level.name for level in RecordingQuality]

    # Ensure the field exists first.
    body = request.get_json()
    field = body.get('quality')
    # Reject requests with invalid arugm
    if not (field in (None, *levels)):
        abort(400)

    # Update the field!
    phrase = Recording.query.filter_by(id=recording_id).one()
    phrase.quality = field
    db.session.commit()

    return '', 204


@app.route('/static/audio/<filename>')
def send_audio(filename):
    """
    Send a previously transcoded audio file.
    """
    # Fail if we don't recognize the file extension.
    try:
        content_type = AUDIO_MIME_TYPES[Path(filename).suffix]
    except KeyError:
        raise NotFound

    path = Path(app.config['TRANSCODED_RECORDINGS_PATH'])
    assert path.resolve().is_dir()
    return send_from_directory(fspath(path), filename,
                               mimetype=content_type)


# ########################### Template utilities ########################### #

@app.template_filter('audio_url')
def audio_url_filter(rec: Recording) -> str:
    """
    Filter that returns a url to the compressed audio file for this particular
    recording.

    Usage (in a template):

        <source src="{{ recording | audio_url }}" type="audio/aac" />
    """
    return url_for('send_audio', filename=f"{rec.id}.m4a")


@app.context_processor
def inject_user():
    """
    Ensures `user` is usable in the template.
    """
    return dict()


@app.template_test(name='logged_in')
def is_logged_in(user):
    return False
