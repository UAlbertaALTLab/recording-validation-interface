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
Fixtures and magic for pytests.
"""

import os
from datetime import datetime
from multiprocessing import Process
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest  # type: ignore
import requests

# Where are fixture files located?
fixtures_dir = Path(__file__).parent / 'fixtures'


@pytest.fixture
def app():
    """
    Yield an active Flask app context.
    """
    from recval.app import app as _app
    with _app.app_context():
        yield _app


@pytest.fixture
def _temporary_data_directory():
    """
    Yields an absolute path to a temporary data directory for storing
    databases and other files.
    """
    with TemporaryDirectory() as tempdir_name:
        path = Path(tempdir_name).resolve()
        yield path


@pytest.fixture
def db(app, _temporary_data_directory):
    """
    Yields a database object bound to an active app context.
    The database starts empty, and is cleared of all data at the end of the
    test.

    Based on http://alextechrants.blogspot.ca/2014/01/unit-testing-sqlalchemy-apps-part-2.html
    """
    from recval.model import db

    # Store the database in a temporary directory.
    db_filename = _temporary_data_directory / 'recval.db'
    assert not db_filename.exists()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_filename}'
    print("Database in", db_filename)

    # place audio in temporary directory.
    audio_dir = _temporary_data_directory / 'audio'
    audio_dir.mkdir()
    app.config['TRANSCODED_RECORDINGS_PATH'] = audio_dir

    # Setup the database.
    db.create_all()
    db.session.flush()
    db.session.expunge_all()
    db.session.commit()

    yield db

    # Tear down the database.
    db.session.rollback()
    db.drop_all()
    db.session.flush()
    db.session.expunge_all()


@pytest.fixture
def client(app, db):
    yield app.test_client()


@pytest.fixture
def acimosis(db, wave_file_path, recording_session):
    """
    Inserts the word 'acimosis'/'puppy' into the database.

    Returns the phrase.id of the inserted phrase.
    """
    from recval.model import Word, Recording
    word = Word(transcription='acîmosis', translation=' puppy  ')
    recording = Recording.new(phrase=word,
                              session=recording_session,
                              fingerprint='acimosis',
                              input_file=wave_file_path,
                              speaker='NIL')
    # Insert it for the first time.
    db.session.add(recording)
    db.session.commit()
    return word.id


@pytest.fixture
def recording_session():
    """
    A session for recordings.
    """
    from datetime import date
    from recval.model import RecordingSession
    from recval.recording_session import SessionID, TimeOfDay
    return RecordingSession.from_session_id(SessionID(
        date=date(2015, 12, 4),
        time_of_day=TimeOfDay.MORNING,
        location=None,
        subsession=None
    ))


@pytest.fixture
def wave_file_path():
    """
    A recording saying "acimosis" (puppy), for use in test cases.
    """
    test_wav = fixtures_dir / 'test.wav'
    assert test_wav.exists()
    return test_wav


@pytest.fixture
def metadata_csv_file():
    """
    Returns a file-like object that is some sample metadata, as downloaded
    from Google Sheets.
    """
    with open(fixtures_dir / 'test_metadata.csv') as csvfile:
        yield csvfile


class MockServer:
    _process: Process

    def __init__(self, app, port=5000) -> None:
        super().__init__()
        self.port = port
        self.app = app
        self.url = "http://localhost:%s" % self.port

    def stop(self) -> None:
        from signal import SIGTERM
        if not hasattr(self, '_process') or self._process.pid is None:
            raise RuntimeError('Tried to shutdown server that has not been started')
        os.killpg(self._process.pid, SIGTERM)

    def start(self):
        import time

        def start_server():
            # Set the session ID so that we can terminate ALL of child
            # processes easily:
            # See: https://pymotw.com/2/subprocess/#process-groups-sessions
            os.setsid()
            self.app.run(port=self.port, use_reloader=False)
        self._process = Process(target=start_server)
        self._process.start()
        # Wait a bit for the server to start
        time.sleep(0.125)


# Derived from: https://stackoverflow.com/a/43882437/6626414
class SessionWithUrlBase(requests.Session):
    # In Python 3 you could place `url_base` after `*args`, but not in Python 2.
    def __init__(self, url_base=None, *args, **kwargs):
        super(SessionWithUrlBase, self).__init__(*args, **kwargs)
        self.url_base = url_base

    def request(self, method, url, **kwargs):
        # Next line of code is here for example purposes only.
        # You really shouldn't just use string concatenation here,
        # take a look at urllib.parse.urljoin instead.
        modified_url = self.url_base + url

        return super(SessionWithUrlBase, self).request(method, modified_url, **kwargs)


@pytest.fixture
def mock_server_thread(app):
    """
    Starts a mock development server on port 8008. Yields a thread.
    Use mock_server as convenient wrapper to make requests to this.
    """
    server = MockServer(app, port=8008)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def mock_server(db, mock_server_thread):
    """
    Starts a development server with an initialized database, and returns a
    requests.Session that will prepend the development server URL whenever
    making a request.

    Usage:

        def test_something(mock_server):
            r = mock_server.get(url_for('homepage'))
            assert r.status_code == 200
    """
    with SessionWithUrlBase(url_base=mock_server_thread.url) as s:
        yield s


@pytest.fixture
def url_for(app):
    """
    Exactly like flask.url_for, except always ensures an app context is setup.
    (That is, will never crash in tests).
    """

    def url_for(*args, **kwargs):
        from flask import url_for  # type: ignore
        with app.test_request_context():
            return url_for(*args, **kwargs)
    return url_for
