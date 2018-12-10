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

import os
import random
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest  # type: ignore
from django.shortcuts import reverse  # type: ignore
from django.test import Client  # type: ignore
from model_mommy import mommy  # type: ignore
from model_mommy.recipe import Recipe  # type: ignore
from pydub import AudioSegment  # type: ignore

from validation.models import Phrase, Recording, Speaker

MAX_RECORDING_LENGTH = 2 ** 31 - 1


@pytest.mark.django_db
def test_serve_recording(client, exported_recording):
    """
    Test that a recording is served properly.
    """
    recording, file_contents = exported_recording
    page = client.get(reverse('validation:recording', kwargs={'recording_id': recording.id}))
    assert page.status_code == 200
    assert page.get('Content-Type') == 'audio/m4a'
    content = b''.join(page.streaming_content)
    assert content == file_contents
    assert content[4:12] == b'ftypM4A ', "Did not serve an .m4a file."

    # Check stuff involving caching.
    assert 'max-age=' in page.get('Cache-Control')
    assert 'public' in page.get('Cache-Control')
    assert 'must-revalidate' not in page.get('Cache-Control')
    assert page.get('ETag').startswith('"'), "Incorrect ETag syntax"
    assert page.get('ETag').endswith('"'), "Incorrect ETag syntax"
    assert page.get('ETag').strip('"') in recording.id, "The ETag should be based on the recording ID"


@pytest.mark.django_db
def test_search_recordings(client):
    phrase = mommy.make(Phrase, transcription='ê-nipat')
    speaker = mommy.make(Speaker, gender=random_gender)

    # Make two recordings. We want to make sure the query actually works by
    # only retrieving the *relevant* recording.
    recipe = Recipe(Recording, timestamp=random_timestamp)
    recording = recipe.make(phrase=phrase, speaker=speaker)
    unrelated_recording = recipe.make()

    assert recording.phrase != unrelated_recording.phrase

    response = client.get(reverse('validation:search_recordings',
                                  kwargs={'query': phrase.transcription}))

    recordings = response.json()
    assert isinstance(recordings, list)
    assert len(recordings) == 1
    recording = recordings[0]
    assert recording.get('wordform') == phrase.transcription
    assert 'speaker' in recording.keys()
    assert recording.get('gender') in 'MF'
    assert recording.get('recording_url').startswith(('http://', 'https://'))
    assert recording.get('recording_url').endswith('.m4a')


@pytest.mark.django_db
def test_search_recording_not_found(client):
    # Create a valid recording, but make sure we never match it.
    speaker = mommy.make(Speaker, gender=random_gender)
    recording = mommy.make(Recording, speaker=speaker, timestamp=random_timestamp)

    # Make the query never matches the only recording in the database:
    query = recording.phrase.transcription + 'h'
    response = client.get(reverse('validation:search_recordings',
                                  kwargs={'query': query}))

    recordings = response.json()
    assert isinstance(recordings, list)
    assert len(recordings) == 0
    assert response.status_code == 404


# ################################ Fixtures ################################ #

@pytest.fixture
def exported_recording(settings):
    """
    Yields a recording that has been physically saved on a storage medium.

    Yields a tuple of the Recording instance, and a bytes instance of the
    recording's transcoded audio.
    """
    recording = Recipe(Recording, timestamp=random_timestamp).make()

    # Create a REAL audio recording, saved on disk.
    with TemporaryDirectory() as temp_dir_name:
        audio_dir = Path(temp_dir_name)

        # Temporarily override the audio directory name.
        settings.RECVAL_AUDIO_DIR = audio_dir
        audio = AudioSegment.empty()
        filename = audio_dir / f'{recording.id}.m4a'
        # Create an actual, bona fide M4A file.
        audio.export(os.fspath(filename), format='ipod')
        file_contents = filename.read_bytes()

        yield recording, file_contents


def random_timestamp():
    return random.randint(0, MAX_RECORDING_LENGTH)


def random_gender():
    return random.choice('MF')
