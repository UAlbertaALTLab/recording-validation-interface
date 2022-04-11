#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright 2018 Eddie Antonio Santos <easantos@ualberta.ca>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Django management command to import recordings. This assumes the database has
been created.
Its defaults are configured using the following settings:
    MEDIA_ROOT
    RECVAL_AUDIO_PREFIX
    RECVAL_METADATA_PATH
    RECVAL_SESSIONS_DIR
See recvalsite/settings.py for more information.
"""
from os import fspath
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand  # type: ignore
from pydub import AudioSegment

from librecval.transcode_recording import transcode_to_aac
from recvalsite import settings
from validation.models import Speaker


class Command(BaseCommand):
    help = "imports Jean's bios into the database"

    def handle(self, *args, **kwargs) -> None:
        speaker = Speaker.objects.get(code="OKI")
        audio_dir = settings.OKIMASIS_BIOS_AUDIO_DIR
        with open(f"{audio_dir}/jean_bio_cree.txt") as f:
            content = f.read()
            speaker.source_bio_text = content

        with open(f"{audio_dir}/jean_bio_eng.txt") as f:
            content = f.read()
            speaker.target_bio_text = content

        speaker.save()

        for audio_file in [
            f"{audio_dir}/jean_bio_eng.mp3",
            f"{audio_dir}/jean_bio_cree.mp3",
        ]:
            audio = AudioSegment.from_file(fspath(audio_file))
            audio = audio.set_channels(1)

            sound_bite = audio.normalize(headroom=0.1)
            rec_name = Path(audio_file).name

            with TemporaryDirectory() as audio_dir:
                recording_path = Path(settings.RECVAL_AUDIO_PREFIX) / Path(
                    f"{rec_name}.m4a"
                )

                transcode_to_aac(
                    sound_bite,
                    recording_path,
                    tags=dict(
                        title=rec_name,
                        artist=speaker,
                        language="crk",
                    ),
                )

                audio_data = recording_path.read_bytes()
                django_file = ContentFile(audio_data, name=recording_path.name)

                if "cree" in audio_file:
                    speaker.source_bio_audio = django_file
                    speaker.save()
                if "eng" in audio_file:
                    speaker.target_bio_audio = django_file
                    speaker.save()
