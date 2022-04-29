import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import logme
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db.models import Q
from pydub import AudioSegment
from tqdm import tqdm

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
        filepath = Path(settings.RECVAL_SEMANTIC_DIR)

        data = {}
        for filename in tqdm(filepath.iterdir()):
            if filename.suffix == ".txt":
                with open(filename) as f:
                    lines = f.readlines()
                    rapid_words_class = "None"
                    for line in lines:
                        phrase = ""
                        if line[0] in [
                            "1",
                            "2",
                            "3",
                            "4",
                            "5",
                            "6",
                            "7",
                            "8",
                            "9",
                            "0",
                        ]:
                            rapid_words_class = line
                            rapid_words_class = rapid_words_class.replace("\n", "")

                        elif "=" in line:
                            split_line = line.split("=")
                            word = split_line[1]
                            split_word = word.split(" ")
                            for w in split_word:
                                if not w:
                                    continue
                                if w[0] in [
                                    "a",
                                    "b",
                                    "c",
                                    "d",
                                    "e",
                                    "f",
                                    "g",
                                    "h",
                                    "i",
                                    "j",
                                    "k",
                                    "l",
                                    "m",
                                    "n",
                                    "o",
                                    "p",
                                    "q",
                                    "r",
                                    "s",
                                    "t",
                                    "u",
                                    "v",
                                    "w",
                                    "x",
                                    "y",
                                    "z",
                                ]:
                                    phrase += w + " "
                                else:
                                    break
                            phrase = phrase.replace("\n", "").strip()
                            phrases = phrase.split(";")
                            phrases.append(split_line[0].strip())
                            if rapid_words_class not in data:
                                data[rapid_words_class] = []
                            data[rapid_words_class].extend([p for p in phrases if p])

        for _class in tqdm(data):
            semantic_class, created = SemanticClass.objects.get_or_create(
                source=SemanticClass.ELICIT,
                origin=SemanticClass.RW,
                classification=_class,
            )
            for word in data[_class]:
                phrases = Phrase.objects.filter(
                    Q(transcription=word) | Q(field_transcription=word)
                )
                for phrase in phrases:
                    phrase.semantic_class.add(semantic_class)
                    phrase.save()
