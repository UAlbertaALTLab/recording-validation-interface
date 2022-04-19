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
from librecval.recording_session import parse_metadata
from librecval.transcode_recording import transcode_to_aac
from validation.models import (
    Speaker,
    RecordingSession,
    Phrase,
    Recording,
    LanguageVariant,
    SemanticClass,
)


class Command(BaseCommand):
    help = "Find the semantic class from metadata"

    def handle(self, *args, **options):
        metadata_filename = settings.RECVAL_METADATA_PATH
        with open(metadata_filename) as metadata_csv:
            metadata = parse_metadata(metadata_csv)

        phrases = []
        for session in metadata.keys():
            session_object, created = RecordingSession.get_or_create_by_session_id(
                session
            )
            if created:
                session_object.delete()
            else:
                recordings = Recording.objects.filter(session=session_object)
                for recording in recordings:
                    phrases.append((recording.phrase, session))

        for phrase in phrases:
            _phrase = phrase[0]
            session = phrase[1]
            info = metadata[session]
            for _class in info["rapid_words"]:
                semantic_class, created = SemanticClass.objects.get_or_create(
                    classification=_class.replace(",", ""),
                    origin=SemanticClass.RW,
                    source=SemanticClass.META,
                )
                _phrase.semantic_class.add(semantic_class)
                _phrase.save()
                print(f"Added {_class} to {_phrase}")
