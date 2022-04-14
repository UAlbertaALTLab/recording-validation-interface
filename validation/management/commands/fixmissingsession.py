import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import logme
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from pydub import AudioSegment

from librecval.extract_auto import SynthesizedRecordingExtractor
from librecval.extract_pfn import PfnRecordingExtractor
from librecval.extract_tsuutina import TsuutinaRecordingExtractor, Segment
from librecval.extract_tvpd import TvpdRecordingExtractor
from librecval.recording_session import SessionID
from librecval.transcode_recording import transcode_to_aac
from validation.models import (
    Speaker,
    RecordingSession,
    Phrase,
    Recording,
    LanguageVariant,
)


class Command(BaseCommand):
    help = "Add sessions to user-submitted entries"

    def handle(self, *args, **options):
        recordings = Recording.objects.filter(session_id=None)
        print(recordings)
        for rec in recordings:
            try:
                historical_recording = Recording.history.filter(id=rec.id).first()
                print(historical_recording.history_date)
                session_id = SessionID(
                    date=datetime.strptime(
                        historical_recording.history_date.split()[0], "%Y-%m-%d"
                    ),
                    time_of_day=None,
                    subsession=None,
                    location=None,
                )
            except AttributeError as e:
                session_id = SessionID(
                    date=datetime.strptime("2022-04-14", "%Y-%m-%d"),
                    time_of_day=None,
                    subsession=None,
                    location=None,
                )

            rec_session, created = RecordingSession.get_or_create_by_session_id(
                session_id
            )
            rec.session_id = rec_session.id
            rec.save()
