#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright 2024 Felipe Bañados Schwerter <banadoss@ualberta.ca>
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

from pathlib import Path
import json
import os
import shutil
import re
import logme
from django.urls import reverse
from tqdm import tqdm
from contextlib import closing
from simple_history.utils import bulk_create_with_history

from django.core.management.base import BaseCommand, CommandError  # type: ignore

from validation.models import Recording, Phrase


def has_enough_words(phrase: Phrase, num: int = 3) -> bool:
    return num <= len(phrase.transcription.split())


def best_recording(phrase: Phrase) -> Recording | None:
    # Try to find a best recording, if none just get a random one
    best_candidates = phrase.recording_set.filter(is_best=True)
    if best_candidates.exists():
        return best_candidates.first()
    if phrase.recording_set.filter(quality=Recording.GOOD).exists():
        return phrase.recording_set.filter(quality=Recording.GOOD).order_by("?").first()
    return None


def split_analyses(str: str) -> list[str]:
    ans = []
    for base in [x.strip() for x in str.split(";") if x.strip()]:
        count = base.count("_") + base.replace("(?)", "").strip().count(" ") + 1
        ans.extend(count * [base])
    return ans


@logme.log
def collect_tokens(phrase: Phrase, logger) -> list[str]:
    words = [x for x in phrase.transcription.split() if x != "..." and x != "…"]
    analyses = [
        x.replace(" ", "&#x20;").replace("/", "&sol;")
        for x in split_analyses(phrase.analysis)
    ]
    if 0 < len(analyses) and len(words) != len(analyses):
        url = f"https://speech-db.altlab.app/maskwacis/segment/{phrase.id}"
        logger.warn(
            f"Phrase {url} count of analyses ({(analyses)}) does not match words.  Trying to be kind and getting the first {(words)}"
        )
    analyses.extend(["" for x in words])

    return [f"{w}\t{analyses[i]}" for i, w in enumerate(words)]


def generate_heading(phrase: Phrase) -> str:
    semantic_classes = "|".join(
        [sc.classification for sc in phrase.semantic_classes.all()]
    )
    recording = best_recording(phrase)

    def sanitized(str):
        return " ".join(str.split()).replace('"', "&quot;")

    inputs = [
        "<sentence",
        f'id="{phrase.id}"',
        f'translation="{sanitized(phrase.translation)}"',
        f'transcription="{sanitized(phrase.transcription)}"',
        f'semantic-class="|{semantic_classes}|"',
    ]
    if recording:
        inputs.append(f'recording="{best_recording(phrase).get_absolute_url()}"')
    inputs.append(">")
    return " ".join(inputs)


def generate_sentence_vrt(phrase: Phrase) -> str:
    lines: list[str] = collect_tokens(phrase)
    lines.insert(0, generate_heading(phrase))
    lines.append("</sentence>")
    return "\n".join(lines)


class Command(BaseCommand):
    """
    Collects RapidWords classifications from an importjson file and applies them
    to the entries in a particular language.
    """

    help = "collect RW indices from importjson and apply them to language entries"

    def add_arguments(self, parser):
        parser.add_argument("export_filename", nargs="?", type=Path)
        parser.add_argument(
            "--language-code",
            default="maskwacis",
            help="Code of LanguageVariant to filter entries",
        )

    def handle(self, *args, export_filename, language_code, **options):
        phrases = Phrase.objects.filter(language__code=language_code).distinct()

        sentences = [x for x in phrases if has_enough_words(x)]

        with open(export_filename, "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
            for sentence in sentences:
                f.write(f"{generate_sentence_vrt(sentence)}\n")
