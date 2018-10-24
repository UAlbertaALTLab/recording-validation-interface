#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Django management command to import recordings. This assumes the database has
been created
"""

from django.core.management.base import BaseCommand, CommandError  # type: ignore
from validation.models import Phrase

from librecval import REPOSITORY_ROOT
from librecval.import_recordings import initialize as import_recordings
from librecval.extract_phrases import RecordingInfo
from pathlib import Path


class Command(BaseCommand):
    help = "imports recordings into the database"

    def add_arguments(self, parser):
        parser.add_argument('session_dir', nargs='?', type=Path, default=None)

    def handle(self, *args, **options):
        self.stdout.write(str(options))
        # Get these from settings?
        sessions_dir = options.get('session_dir', DEFAULT_SESSION_DIR)
        # Now, import all those recordings!
        import_recordings(directory=session_dir,
                          transcoded_recordings_path=...,
                          repository_root=REPOSITORY_ROOT,
                          metadata_filename=REPOSITORY_ROOT / 'etc' / 'metadata.csv',
                          import_recording=django_recording_importer)


def django_recording_importer(info: RecordingInfo, rec_id: str, recording_path: Path) -> None:
    """
    Imports a single recording.
    """
    print(info)
