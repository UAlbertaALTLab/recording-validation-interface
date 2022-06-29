from django.core.management.base import BaseCommand
from tqdm import tqdm

from validation.models import SemanticClass, Phrase


class Command(BaseCommand):
    help = "adds semantic classes to the database"

    def handle(self, *args, **options):
        semantic_classes = SemanticClass.objects.all()
        for s_class in tqdm(semantic_classes):
            other_classes = SemanticClass.objects.filter(
                classification=s_class.classification
            )
            if len(other_classes) > 1:
                for other_class in other_classes:
                    if other_class == s_class:
                        continue
                    phrases = Phrase.objects.filter(semantic_class=other_class)
                    for phrase in phrases:
                        phrase.semantic_class.add(s_class)
                    other_class.delete()
