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

from librecval.normalization import normalize_sro
from validation.models import Phrase

from tqdm import tqdm
import csv


class Command(BaseCommand):
    help = "Determines if the phrase is already in the Maskwacîs dictionary"

    def handle(self, *args, **options):
        """
        Iterates over all the phrases in the database
        and sets the origin to "MD" if there is an exact match for
        that word in the treatedMD.csv file
        """
        md_words = get_md_words()
        phrases = Phrase.objects.all()
        for phrase in tqdm(phrases.iterator(), total=phrases.count()):
            normalized = normalize_sro(phrase.transcription)
            normalized = remove_diacritics(normalized)
            if normalized in md_words:
                phrase.origin = "MD"
                phrase.translation = md_words[normalized]
            else:
                phrase.origin = "new"
            phrase.save()


def get_md_words():
    """
    Gets the words from the Maskwacîs dictionary file
    :return: a dict of Cree words and their translations
    """
    words = {}
    with open("private/treatedMD.csv", "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            words[row["SRO"]] = row["MeaningInEnglish"]

    return words


def remove_diacritics(word):
    word = word.replace("ê", "e")
    word = word.replace("î", "i")
    word = word.replace("â", "a")
    word = word.replace("ô", "o")

    return word
