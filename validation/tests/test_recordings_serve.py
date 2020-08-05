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
from model_bakery import baker  # type: ignore
from pydub import AudioSegment  # type: ignore

from validation.models import Recording


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


@pytest.mark.django_db
def test_serve_recording_partial_content(client, exported_recording):
    """
    Test that a recording is served properly.
    """
    recording, file_contents = exported_recording
    page = client.get(
        reverse("validation:recording", kwargs={"recording_id": recording.id}),
        # Safari likes sending this value for some reason:
        HTTP_RANGE="bytes=0-1",
    )

    content_length = len(file_contents)

    len_of_first_request = 2

    assert page.status_code == 206
    assert "bytes" in page.get("Accept-Ranges")
    assert page.get("Content-Type") == "audio/m4a"
    assert page.get("Content-Range") == f"bytes 0-1/{content_length}"
    assert int(page.get("Content-Length")) == len_of_first_request
    content = b"".join(page.streaming_content)
    assert content == file_contents[0:len_of_first_request]

    # Get the rest of the file
    index_of_last_byte = content_length - 1
    page = client.get(
        reverse("validation:recording", kwargs={"recording_id": recording.id}),
        HTTP_RANGE=f"bytes=2-{index_of_last_byte}",
    )

    assert page.status_code == 206
    assert page.get("Content-Range") == f"bytes 2-{index_of_last_byte}/{content_length}"
    assert int(page.get("Content-Length")) == content_length - len_of_first_request
    rest_content = b"".join(page.streaming_content)
    assert content + rest_content == file_contents


@pytest.mark.django_db
def test_serve_recording_partial_content_open_range(client, exported_recording):
    """
    Chrome will make this request
    """
    recording, file_contents = exported_recording
    page = client.get(
        reverse("validation:recording", kwargs={"recording_id": recording.id}),
        HTTP_RANGE="bytes=0-",
    )

    assert page.status_code in (200, 206)
    assert int(page.get("Content-Length")) == len(file_contents)
    content = b"".join(page.streaming_content)
    assert content == file_contents


# ################################ Fixtures ################################ #


@pytest.fixture
def exported_recording(settings):
    """
    Yields a recording that has been physically saved on a storage medium.

    Yields a tuple of the Recording instance, and a bytes instance of the
    recording's transcoded audio.
    """
    recording = baker.make_recipe("validation.recording")

    # Create a REAL audio recording, saved on disk.
    with TemporaryDirectory() as temp_dir_name:
        media_dir = Path(temp_dir_name)

        # Temporarily override the audio directory name.
        settings.MEDIA_ROOT = media_dir
        audio_dir = Recording.get_path_to_audio_directory()
        audio_dir.mkdir(parents=True)

        # This try/except a dumb way of asserting that
        # audio_dir is a descendant of media_dir.
        try:
            audio_dir.relative_to(media_dir)
        except ValueError:
            raise

        audio = AudioSegment.empty()
        filename = audio_dir / f"{recording.id}.m4a"
        # Create an actual, bona fide M4A file.
        # TODO: use librecval.transcode_recording?
        audio.export(os.fspath(filename), format="ipod", parameters=["-strict", "-2"])
        file_contents = filename.read_bytes()

        yield recording, file_contents
