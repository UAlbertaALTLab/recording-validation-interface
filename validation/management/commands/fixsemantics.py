from django.core.management.base import BaseCommand
from tqdm import tqdm

from validation.models import (
    SemanticClass,
)


class Command(BaseCommand):
    help = "adds semantic classes to the database"

    def handle(self, *args, **options):
        semantic_classes = SemanticClass.objects.all()
        for s_class in tqdm(semantic_classes):
            if "_" in s_class.classification:
                new_class = s_class.classification.replace("_", " ")
                s_class.classification = new_class
                s_class.save()
