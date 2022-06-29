from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from tqdm import tqdm

from validation.models import (
    Phrase,
    SemanticClass,
)


class Command(BaseCommand):
    help = "Populate the hypernym and hyponym fields of the semantic class"

    def handle(self, *args, **options):
        classes = SemanticClass.objects.all()
        for c in tqdm(classes):
            name = c.classification
            name = name.replace("_", " ")
            name = name.split()
            if len(name) < 1:
                continue

            number = name[0]
            iter_classes = SemanticClass.objects.all()
            for s_class in iter_classes:
                if s_class.classification.startswith(number):
                    if s_class != c:
                        s_class.hypernyms.add(c)
                        c.hyponyms.add(s_class)
                        c.save()
                        s_class.save()
