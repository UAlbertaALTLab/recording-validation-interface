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
Unit/Integration tests serving recordings.

Note: if things get slow, the recordings should be served by a static file
server like Apache or Nginx.
"""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest  # type: ignore
from django.shortcuts import reverse  # type: ignore
from model_mommy import mommy  # type: ignore
from pydub import AudioSegment  # type: ignore


@pytest.mark.django_db
def test_serve_recording(client, exported_recording):
    """
    Test that a recording is served properly.
    """
    recording, file_contents = exported_recording
    page = client.get(
        reverse("validation:recording", kwargs={"recording_id": recording.id})
    )
    assert page.status_code == 200
    assert page.get("Content-Type") == "audio/m4a"
    content = b"".join(page.streaming_content)
    assert content == file_contents
    assert content[4:12] == b"ftypM4A ", "Did not serve an .m4a file."

    # Make sure that caching is set up, and sufficiently aggressive.
    assert "max-age=" in page.get("Cache-Control")
    assert "public" in page.get("Cache-Control")
    assert "must-revalidate" not in page.get("Cache-Control")
    # TODO: last modified date?
    assert page.get("ETag").startswith('"'), "Incorrect ETag syntax"
    assert page.get("ETag").endswith('"'), "Incorrect ETag syntax"
    assert (
        page.get("ETag").strip('"') in recording.id
    ), "The ETag should be based on the recording ID"


# ################################ Fixtures ################################ #


@pytest.fixture
def exported_recording(settings):
    """
    Yields a recording that has been physically saved on a storage medium.

    Yields a tuple of the Recording instance, and a bytes instance of the
    recording's transcoded audio.
    """
    recording = mommy.make_recipe("validation.recording")

    # Create a REAL audio recording, saved on disk.
    with TemporaryDirectory() as temp_dir_name:
        audio_dir = Path(temp_dir_name)

        # Temporarily override the audio directory name.
        settings.RECVAL_AUDIO_DIR = audio_dir
        audio = AudioSegment.empty()
        filename = audio_dir / f"{recording.id}.m4a"
        # Create an actual, bona fide M4A file.
        # TODO: use librecval.transcode_recording?
        audio.export(os.fspath(filename), format="ipod", parameters=["-strict", "-2"])
        file_contents = filename.read_bytes()

        yield recording, file_contents
