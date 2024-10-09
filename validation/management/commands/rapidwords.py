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
from tqdm import tqdm
from contextlib import closing
from simple_history.utils import bulk_create_with_history

from django.core.management.base import BaseCommand, CommandError  # type: ignore

from validation.models import SemanticClass, Phrase, SemanticClassAnnotation


def semantic_classes(indices):
    candidates = SemanticClass.objects.filter(collection=SemanticClass.RW)
    return [candidates.get(classification__startswith=index + " ") for index in indices]


def head_cleanup(head):
    candidate = head.strip()
    return re.sub(r"^'", "", re.sub(r"(\?|\!|\'|\.)$", "", candidate))


class Command(BaseCommand):
    """
    Collects RapidWords classifications from an importjson file and applies them
    to the entries in a particular language.
    """

    help = "collect RW indices from importjson and apply them to language entries"

    def add_arguments(self, parser):
        parser.add_argument("importjson_path", nargs="?", type=Path)
        parser.add_argument(
            "--language-code",
            default="maskwacis",
            help="Code of LanguageVariant to filter entries",
        )

    def handle(self, *args, importjson_path, language_code, **options):
        # Change this if the raw audio files exist elsewhere!
        print("Loading importjson...")
        with open(importjson_path, "r") as f:
            importjson = json.load(f)

        rapidwords = {}
        slugs = {}
        RapidWord = SemanticClass.objects.filter(collection=SemanticClass.RW)
        valid_categories = {x.classification.split(" ")[0]: x for x in RapidWord}

        def nearest_index(category):
            candidate = category
            while len(candidate) > 0:
                if candidate in valid_categories:
                    return candidate
                candidate = candidate[: candidate.rfind(".")]
            return None

        print(f"RW has {len(valid_categories)} valid categories in the database.")
        print(f"Collecting Semantic Classes in database for importjson...")
        invalid_rapidwords = set()
        for entry in tqdm(importjson, total=len(importjson)):
            if "linguistInfo" in entry.keys():
                content = entry["linguistInfo"]["rw_indices"]
                slug = slugs.setdefault(entry["slug"], {})
                head = rapidwords.setdefault(head_cleanup(entry["head"]), {})
                for source, rw_indices in content.items():
                    candidates = [
                        valid_categories[index]
                        for index in rw_indices
                        if index in valid_categories
                    ]
                    slug.setdefault(source, set()).update(candidates)
                    head.setdefault(source, set()).update(candidates)
                    failures = [
                        index for index in rw_indices if index not in valid_categories
                    ]
                    invalid_rapidwords.update(failures)

        print(
            f"Set of invalid rapidword annotations in sources is {invalid_rapidwords}  Matching the nearest one that fits..."
        )
        valid_super = {
            index: valid_categories[nearest_index(index)]
            for index in invalid_rapidwords
            if nearest_index(index)
        }
        print(
            f"Found {len(valid_super)} candidates with less precise valid candidates."
        )
        for entry in tqdm(importjson, total=len(importjson)):
            if "linguistInfo" in entry.keys():
                content = entry["linguistInfo"]["rw_indices"]
                slug = slugs.setdefault(entry["slug"], {})
                head = rapidwords.setdefault(head_cleanup(entry["head"]), {})
                for source, rw_indices in content.items():
                    failures = [
                        valid_super[index]
                        for index in rw_indices
                        if index in valid_super
                    ]
                    slug.get(source).update(failures)
                    head.get(source).update(failures)

        print("Collecting extra categories via formOf annotations...")

        for entry in tqdm(importjson, total=len(importjson)):
            formOf = entry.get("formOf", None)
            if formOf:
                content = slugs[formOf]
                head = rapidwords.setdefault(head_cleanup(entry["head"]), {})
                for source, rw_indices in content.items():
                    head.setdefault(source, set()).update(rw_indices)

        print(
            f"RapidWords source data collected with {len(rapidwords.keys())} entries."
        )
        md_entries = {
            key: entry.get("MD")
            for key, entry in rapidwords.items()
            if 0 < len(entry.get("MD", []))
        }
        cw_entries = {
            key: entry.get("CW")
            for key, entry in rapidwords.items()
            if 0 < len(entry.get("CW", []))
        }
        print(f"Rapidwords source data with MD RW in {len(md_entries.keys())} entries.")
        print(f"Rapidwords source data with CW RW in {len(cw_entries.keys())} entries.")

        spaced_keys = {
            key
            for key in rapidwords.keys()
            if " " in key
            and 0 < len(rapidwords[key]["CW"]) + len(rapidwords[key]["MD"])
        }

        print(
            f"Annotating ALL entries with Rapidwords, prioritizing MD annotations over CW..."
        )
        print(f"Spaced keys: {len(spaced_keys)}")
        # What do we do for multiple entries in either dict?  My gut is to just add all of them and then manually check which ones work.
        # Do we want to check as well for prefixes and postfixes inside each word?

        phrases = Phrase.objects.filter(language__code=language_code)
        print(f"Processing {phrases.count()} phrase objects...")
        candidate_annotations = []
        for phrase in tqdm(phrases.iterator(), total=phrases.count()):
            tokens = set(phrase.transcription.split(" "))
            if len(tokens) == 1:
                if language_code == "maskwacis" and md_entries.get(
                    head_cleanup(phrase.transcription), None
                ):
                    for entry in md_entries.get(head_cleanup(phrase.transcription)):
                        candidate_annotations.append(
                            SemanticClassAnnotation(
                                phrase=phrase,
                                semantic_class=entry,
                                source=SemanticClassAnnotation.DICTIONARY,
                                dictionary_source=SemanticClassAnnotation.MD,
                            )
                        )
                    SemanticClassAnnotation.objects.filter(
                        phrase=phrase, semantic_class__collection=SemanticClass.RW
                    ).delete()

                elif cw_entries.get(head_cleanup(phrase.transcription), None):
                    for entry in cw_entries.get(head_cleanup(phrase.transcription)):
                        candidate_annotations.append(
                            SemanticClassAnnotation(
                                phrase=phrase,
                                semantic_class=entry,
                                source=SemanticClassAnnotation.DICTIONARY,
                                dictionary_source=SemanticClassAnnotation.CW,
                            )
                        )
                    SemanticClassAnnotation.objects.filter(
                        phrase=phrase, semantic_class__collection=SemanticClass.RW
                    ).delete()

            else:
                # More than 1 token, search and add.
                # First search all multi-word candidates
                local_candidates = []
                multi_words = [
                    rapidwords[key]
                    for key in spaced_keys
                    if key in phrase.transcription
                ]
                for candidate in multi_words:
                    if language_code == "maskwacis" and 0 < len(
                        candidate.get("MD", [])
                    ):
                        for entry in candidate.get("MD", []):
                            local_candidates.append(
                                SemanticClassAnnotation(
                                    phrase=phrase,
                                    semantic_class=entry,
                                    source=SemanticClassAnnotation.DICTIONARY,
                                    dictionary_source=SemanticClassAnnotation.MD,
                                )
                            )
                    elif 0 < len(candidate.get("CW", [])):
                        for entry in candidate.get("CW", []):
                            local_candidates.append(
                                SemanticClassAnnotation(
                                    phrase=phrase,
                                    semantic_class=entry,
                                    source=SemanticClassAnnotation.DICTIONARY,
                                    dictionary_source=SemanticClassAnnotation.CW,
                                )
                            )
                # Now add all the single-word candidates:
                for token in tokens:
                    if language_code == "maskwacis" and md_entries.get(
                        head_cleanup(token), []
                    ):
                        for entry in md_entries.get(head_cleanup(token)):
                            local_candidates.append(
                                SemanticClassAnnotation(
                                    phrase=phrase,
                                    semantic_class=entry,
                                    source=SemanticClassAnnotation.DICTIONARY,
                                    dictionary_source=SemanticClassAnnotation.MD,
                                )
                            )

                    elif cw_entries.get(head_cleanup(token), []):
                        for entry in cw_entries.get(head_cleanup(token)):
                            local_candidates.append(
                                SemanticClassAnnotation(
                                    phrase=phrase,
                                    semantic_class=entry,
                                    source=SemanticClassAnnotation.DICTIONARY,
                                    dictionary_source=SemanticClassAnnotation.CW,
                                )
                            )
                # Now only add those not already there...
                current_phrase_rapidwords = phrase.semantic_classes.filter(
                    collection=SemanticClass.RW
                )
                for candidate in local_candidates:
                    if candidate.semantic_class not in current_phrase_rapidwords:
                        candidate_annotations.append(candidate)

        print(f"Creating {len(candidate_annotations)} annotations...")
        bulk_create_with_history(
            candidate_annotations,
            SemanticClassAnnotation,
            batch_size=500,
            default_change_reason="Imported from importjson",
        )
