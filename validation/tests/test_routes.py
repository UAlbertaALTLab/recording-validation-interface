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

import random

import pytest  # type: ignore
from django.shortcuts import reverse  # type: ignore
from django.test import Client  # type: ignore
from model_mommy.recipe import Recipe  # type: ignore
from pydub import AudioSegment  # type: ignore

from validation.models import Recording

MAX_RECORDING_LENGTH = 2 ** 31 - 1


@pytest.mark.django_db
def test_serve_recording(exported_recording):
    """
    Test that a recording is served properly.
    """
    recording, file_contents = exported_recording
    client = Client()
    page = client.get(reverse('validation:recording', kwargs={'recording_id': recording.id}))
    assert page.status_code == 200
    assert page.get('Content-Type') == 'audio/m4a'
    assert page.content == file_contents


@pytest.fixture
def exported_recording():
    recording = Recipe(Recording, timestamp=random_timestamp).make()

    # Create a REAL audio recording, saved on disk.
    # XXX: bad, temporary, figure out a better way!
    from django.conf import settings  # type: ignore
    audio = AudioSegment.empty()
    filename = settings.RECVAL_AUDIO_DIR / f'{recording.id}.m4a'
    audio.export(str(filename))
    file_contents = filename.read_bytes()

    yield recording, file_contents

    # Clean up!
    filename.unlink()


def random_timestamp():
    return random.randint(0, MAX_RECORDING_LENGTH)
