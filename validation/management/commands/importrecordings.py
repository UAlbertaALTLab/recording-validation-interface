#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Django management command to import recordings. This assumes the database has
been created.

Its defaults are configured using the following settings:

    RECVAL_SESSIONS_DIR
    RECVAL_AUDIO_DIR
    RECVAL_METADATA_PATH

See recvalsite/settings.py for more information.
"""

from pathlib import Path

import logme  # type: ignore

from django.conf import settings  # type: ignore
from django.core.management.base import BaseCommand, CommandError  # type: ignore

from librecval import REPOSITORY_ROOT
from librecval.import_recordings import initialize as import_recordings
from librecval.extract_phrases import RecordingInfo
from validation.models import Phrase


class Command(BaseCommand):
    help = "imports recordings into the database"

    def add_arguments(self, parser):
        parser.add_argument('sessions_dir', nargs='?', type=Path, default=None)

    def handle(self, *args, **options) -> None:
        # Get these from settings?
        sessions_dir = options.get('session_dir', settings.RECVAL_SESSIONS_DIR)
        # Now, import all those recordings!
        import_recordings(directory=sessions_dir,
                          transcoded_recordings_path=settings.RECVAL_AUDIO_DIR,
                          metadata_filename=settings.RECVAL_METADATA_PATH,
                          import_recording=django_recording_importer)


@logme.log
def django_recording_importer(info: RecordingInfo, rec_id: str, recording_path: Path, logger) -> None:
    """
    Imports a single recording.
    """
    logger.debug(info)
