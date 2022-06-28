import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from validation.models import (
    Phrase,
    SemanticClass,
)


class Command(BaseCommand):
    help = "adds semantic classes to the database"

    def handle(self, *args, **options):
        filename = settings.RW_FILEPATH
        with open(filename) as f:
            lines = f.readlines()
            for line in tqdm(lines):
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
                    rapid_words_class = rapid_words_class.replace("_", " ")
                    semantic_class, _ = SemanticClass.objects.get_or_create(
                        classification=rapid_words_class,
                        origin=SemanticClass.RW,
                        source=SemanticClass.META,
                    )
