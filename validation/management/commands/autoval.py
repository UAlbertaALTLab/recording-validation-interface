#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright 2021 Jolene Poulin <jcpoulin@ualberta.ca>
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

from django.conf import settings  # type: ignore
from django.core.management.base import BaseCommand

from validation.helpers import (
    perfect_match,
    exactly_one_analysis,
    get_distance_with_translations,
)
from validation.models import Phrase

from tqdm import tqdm


class Command(BaseCommand):
    help = "auto-validates phrases"

    def handle(self, *args, **options):
        """
        Iterates over all the phrases in the database
        and auto-standardizes wordforms where there is exactly one
        matching analysis
        """
        phrases = Phrase.objects.all()
        for phrase in tqdm(phrases.iterator(), total=phrases.count()):
            if not phrase.validated:
                segment_name = phrase.field_transcription
                suggestions = get_distance_with_translations(segment_name)
                match = perfect_match(segment_name, suggestions)

                # only save the analysis if there is exactly one
                if exactly_one_analysis(match):
                    phrase.transcription = match["transcription"]
                    phrase.analysis = match["matches"][0]["analysis"]
                    phrase.status = "auto-validated"
                    phrase.validated = True
                    phrase.save()
