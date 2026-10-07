from datetime import datetime
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
import logme
from pydub import AudioSegment

from librecval.extract_auto import SynthesizedRecordingExtractor
from librecval.extract_pfn import PfnRecordingExtractor
from librecval.extract_tsuutina import Segment, TsuutinaRecordingExtractor
from librecval.extract_tvpd import TvpdRecordingExtractor
from librecval.transcode_recording import transcode_to_aac
from validation.models import (
    LanguageVariant,
    Phrase,
    Recording,
    RecordingSession,
    Speaker,
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
