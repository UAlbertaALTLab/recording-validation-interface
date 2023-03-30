from django.core.management.base import BaseCommand  # type: ignore

from validation.models import Phrase


class Command(BaseCommand):
    help = "looks for the combined ˆ+[aeio] character and replaces it with the single ê character (but the correct vowel)"

    def handle(self, *args, **options) -> None:
        phrases = Phrase.objects.all()
        for phrase in phrases:
            print(phrase.transcription.find(u"ˆ"))
