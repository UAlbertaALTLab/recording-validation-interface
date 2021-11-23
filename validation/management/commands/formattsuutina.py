from django.core.management.base import BaseCommand

from validation.models import Phrase, LanguageVariant, Issue, Speaker


class Command(BaseCommand):
    help = "Formats the TVPD entries in the way that's expected for morphodict"

    def handle(self, *args, **options):
        language = LanguageVariant.objects.get(code="tsuutina")
        phrases = Phrase.objects.filter(language=language)

        for phrase in phrases:
            transcription = phrase.field_transcription
            transcription = transcription.replace(".", "")
            transcription = transcription.lower()
            phrase.transcription = transcription
            phrase.save()
