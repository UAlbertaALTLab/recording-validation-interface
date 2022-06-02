import csv
import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import logme
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from pydub import AudioSegment
from tqdm import tqdm

from librecval.extract_tsuutina import TsuutinaRecordingExtractor, Segment
from librecval.transcode_recording import transcode_to_aac
from validation.models import (
    Speaker,
    RecordingSession,
    Phrase,
    Recording,
    LanguageVariant,
    SemanticClass,
)


class RecordingError(Exception):
    """
    The error that gets raised if something bad happens with the recording.
    """


class Command(BaseCommand):
    help = "adds semantic classes to Tsuut'ina data"

    def handle(self, *args, **options):
        metadata_file = settings.TSUUTINA_METADATA_PATH
        data = {}
        with open(metadata_file) as csvfile:
            spamreader = csv.reader(csvfile, delimiter=",")
            for row in spamreader:
                data[row[0]] = row[15].split(",")[0] + " " + row[16]

        for item in tqdm(data):
            if Phrase.objects.filter(osid=item).exists():
                phrase = Phrase.objects.filter(osid=item).first()
                semantic_class, _ = SemanticClass.objects.get_or_create(
                    source=SemanticClass.META,
                    origin=SemanticClass.RW,
                    classification=data[item],
                )
                phrase.semantic_class.add(semantic_class)
                phrase.save()
