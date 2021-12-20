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
from librecval.transcode_recording import transcode_to_aac
from validation.models import (
    Speaker,
    RecordingSession,
    Phrase,
    Recording,
    LanguageVariant,
)


class Command(BaseCommand):
    help = "I accidentally saved the transcription in the translation field for all the synthesized audio, this command fixes that."

    def handle(self, *args, **options):
        speaker = Speaker.objects.get(code="A-DOL")
        phrases = Phrase.objects.filter(recording__speaker=speaker)
        for phrase in phrases:
            transcription = phrase.translation
            phrase.transcription = transcription
            phrase.translation = ""
            phrase.save()
