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

from pathlib import Path
from tempfile import TemporaryDirectory

import logme  # type: ignore
from django.conf import settings  # type: ignore
from django.core.files.base import ContentFile  # type: ignore
from django.core.management.base import BaseCommand, CommandError  # type: ignore

from librecval import REPOSITORY_ROOT
from librecval.extract_phrases import RecordingInfo
from librecval.import_recordings import initialize as import_recordings
from validation.models import Phrase, Recording, RecordingSession, Speaker


class Command(BaseCommand):
    help = "imports recordings into the database"

    def add_arguments(self, parser):
        parser.add_argument("sessions_dir", nargs="?", type=Path, default=None)

    def handle(self, *args, **options) -> None:
        sessions_dir = options.get("session_dir", settings.RECVAL_SESSIONS_DIR)

        # Store transcoded audio in a temp directory;
        # these files will be then handled by the currently configured storage backend.
        with TemporaryDirectory() as audio_dir:
            # Now, import all those recordings!
            import_recordings(
                directory=sessions_dir,
                transcoded_recordings_path=audio_dir,
                metadata_filename=settings.RECVAL_METADATA_PATH,
                import_recording=django_recording_importer,
            )


@logme.log
def django_recording_importer(
    info: RecordingInfo, recording_path: Path, logger
) -> None:
    """
    Imports a single recording.
    """

    # Recording requires a Speaker, a RecordingSession, and a Phrase.
    # Make those first.
    speaker, speaker_created = Speaker.objects.get_or_create(
        code=info.speaker  # TODO: normalized?
    )
    if speaker_created:
        logger.info("New speaker: %s", speaker)

    session, session_created = RecordingSession.get_or_create_by_session_id(
        info.session
    )
    if session_created:
        logger.info("New session: %s", session)

    phrase, phrase_created = Phrase.objects.get_or_create(
        transcription=info.transcription,
        kind=info.type,
        defaults=dict(translation=info.translation, validated=False, origin=None),
    )
    if phrase_created:
        logger.info("New phrase: %s", phrase)

    # XXX: this is kind of dumb; the compressed audio is written to storage, read again,
    # and will be written back by Django :/
    audio_data = recording_path.read_bytes()
    django_file = ContentFile(audio_data, name=recording_path.name)

    # Finally, we can create the recording.
    recording = Recording(
        id=info.compute_sha256hash(),
        speaker=speaker,
        compressed_audio=django_file,
        timestamp=info.timestamp,
        phrase=phrase,
        session=session,
        quality="",
    )
    recording.clean()

    logger.debug("Saving recording %s", recording)
    recording.save()
