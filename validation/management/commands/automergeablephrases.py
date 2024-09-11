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

import logme  # type: ignore
from django.core.management.base import BaseCommand, CommandError  # type: ignore
from django.db.models import Q, QuerySet, Count

from validation.models import (
    Phrase,
)

from validation.views import handle_merge_phrases


class Command(BaseCommand):
    help = "Merge all the possible entries that, in the same language, have same transcription and translation, and collecting all the info on the other fields when they differ."

    def add_arguments(self, parser):
        parser.add_argument(
            "--merge",
            help="Without this explicit option, the command only lists all candidates.",
            action="store_true",
            default=False,
        )

    def handle(self, *args, merge, **options) -> None:
        # Collect ALL candidates
        duplicate_transcriptions = (
            Phrase.objects.values("transcription")
            .annotate(Count("id"))
            .order_by()
            .filter(id__count__gt=1)
        )
        candidates = []

        for entry in duplicate_transcriptions:
            transcription = entry["transcription"]
            duplicate_translations = (
                Phrase.objects.filter(transcription=transcription)
                .values("translation")
                .annotate(Count("id"))
                .order_by()
                .filter(id__count__gt=1)
            )
            for entry in duplicate_translations:
                translation = entry["translation"]
                candidate_set = Phrase.objects.filter(
                    transcription=transcription, translation=translation
                )
                if candidate_set.count() < 2:
                    continue
                if candidate_set.values("language").distinct().count() > 1:
                    continue
                ids = candidate_set.values("id")
                candidates.append(
                    {
                        "transcription": transcription,
                        "translation": translation,
                        "ids": [entry["id"] for entry in ids],
                    }
                )
        self._handle_merge(candidates, merge)

    @logme.log
    def _handle_merge(self, candidates, merge, logger):
        total_entries = sum([len(c["ids"]) for c in candidates])
        for candidate in candidates:
            if merge and len(candidate["ids"]) > 1:
                logger.warn(f"MERGING {show_candidate(candidate)}")
                handle_merge_phrases(
                    Phrase.objects.get(id=candidate["ids"][0]),
                    Phrase.objects.filter(id__in=candidate["ids"][1:]),
                    True,
                )
            else:
                logger.info(show_candidate(candidate))

        logger.info(
            f"Found a total of {len(candidates)} possible phrases, which {'were' if merge else 'can be'} merged from a total of {total_entries}"
        )
        logger.info("Done.")


def show_candidate(c):
    count = len(c["ids"])
    transcription = c["transcription"]
    translation = c["translation"]
    return f"'{transcription}':'{translation}', mergeable from {count} entries."
