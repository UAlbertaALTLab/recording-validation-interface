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

from django.core.management.base import BaseCommand
from validation.models import Phrase, LanguageVariant, Recording

from tqdm import tqdm
import csv


class Command(BaseCommand):
    help = "Resets all recording quality markings to UNKNOWN to fix an import error on OS content"

    def handle(self, *args, **options):
        """
        Iterates over all the phrases in the database
        and sets the origin to "MD" if there is an exact match for
        that word in the treatedMD.csv file
        """
        language = LanguageVariant.objects.get(code="tsuutina")
        phrases = Phrase.objects.filter(language=language)
        recordings = Recording.objects.filter(phrase__in=phrases)
        for rec in tqdm(recordings.iterator(), total=recordings.count()):
            if rec.quality != Recording.UNKNOWN:
                rec.quality = Recording.UNKNOWN
                rec.save()
