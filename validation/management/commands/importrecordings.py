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
from librecval.extract_phrases import Segment
from librecval.import_recordings import initialize as import_recordings
from validation.models import (
    Phrase,
    Recording,
    RecordingSession,
    Speaker,
    LanguageVariant,
)


class Command(BaseCommand):
    help = "imports recordings into the database"

    def add_arguments(self, parser):
        parser.add_argument("sessions_dir", nargs="?", type=Path, default=None)
        parser.add_argument(
            "--wav",
            action="store_true",
            default=False,
            help="Stores wav files INSTEAD of transcoded m4as",
        )

        parser.add_argument(
            "--skip-db",
            dest="store_db",
            action="store_false",
            default=True,
            help="skips storing in the database (write files only)",
        )

        parser.add_argument(
            "--audio-dir",
            type=Path,
            help="where to store the extracted audio",
            default=Path("./audio"),
        )

    def handle(
        self,
        *args,
        store_db=True,
        wav=False,
        audio_dir: Path = Path("./audio"),
        sessions_dir=None,
        **options
    ) -> None:
        if sessions_dir is None:
            sessions_dir = settings.RECVAL_SESSIONS_DIR

        if store_db:
            self._handle_store_django(sessions_dir)
        else:
            self._handle_store_wav(sessions_dir, audio_dir, wav)

    def _handle_store_wav(
        self, sessions_dir: Path, audio_dir: Path, wav: bool = False
    ) -> None:
        """
        Stores wave files to a specific directory.
        """
        import_recordings(
            directory=sessions_dir,
            transcoded_recordings_path=audio_dir,
            metadata_filename=settings.RECVAL_METADATA_PATH,
            import_recording=null_recording_importer,
            recording_format="wav" if wav else "m4a",
        )

    def _handle_store_django(self, sessions_dir: Path) -> None:
        """
        Stores m4a files, managed by Django's media engine.
        """
        # Store transcoded audio in a temp directory;
        # these files will be then handled by the currently configured storage backend.
        with TemporaryDirectory() as audio_dir:
            # Now, import all those recordings!
            import_recordings(
                directory=sessions_dir,
                transcoded_recordings_path=audio_dir,
                metadata_filename=settings.RECVAL_METADATA_PATH,
                import_recording=django_recording_importer,
                recording_format="m4a",
            )


@logme.log
def django_recording_importer(info: Segment, recording_path: Path, logger) -> None:
    """
    Imports a single recording.
    """

    if Recording.objects.filter(id=info.compute_sha256hash()).exists():
        # This recording is already in the DB, return early
        return

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

    language = LanguageVariant.objects.get(name="Maskwacîs", code="maskwacis")

    phrase, phrase_created = Phrase.objects.get_or_create(
        field_transcription=info.cree_transcription,
        transcription=info.cree_transcription,
        status=Phrase.NEW,
        kind=info.type,
        language=language,
        defaults=dict(
            translation=info.english_translation,
            validated=False,
            origin=Phrase.MASKWACÎS_DICTIONARY,
        ),
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
        timestamp=info.start,
        phrase=phrase,
        session=session,
        quality=info.quality,
        comment=info.comment,
    )
    recording.clean()

    logger.debug("Saving recording %s", recording)
    recording.save()


def null_recording_importer(info: Segment, recording_path: Path) -> None:
    """
    Does nothing!
    """
