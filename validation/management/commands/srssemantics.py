import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from validation.models import (
    Phrase,
    SemanticClass,
)


class Command(BaseCommand):
    help = "adds semantic classes to Tsuut'ina data"

    def handle(self, *args, **options):
        metadata_file = settings.TSUUTINA_METADATA_PATH
        data = {}
        with open(metadata_file) as csvfile:
            spamreader = csv.reader(csvfile, delimiter=",")
            for row in spamreader:
                number = row[15].split(",")[0]
                number = number.split(".")
                number = number[:-1]
                number = ".".join(number)
                data[row[0]] = number + " " + row[16].replace("_", " ")

        for item in tqdm(data):
            if Phrase.objects.filter(osid=item).exists():
                phrase = Phrase.objects.filter(osid=item).first()
                phrase.semantic_class.clear()
                semantic_class, _ = SemanticClass.objects.get_or_create(
                    source=SemanticClass.META,
                    origin=SemanticClass.RW,
                    classification=data[item],
                )
                phrase.semantic_class.add(semantic_class)
                phrase.save()
