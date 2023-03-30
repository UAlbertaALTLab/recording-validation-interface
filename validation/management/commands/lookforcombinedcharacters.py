from django.core.management.base import BaseCommand  # type: ignore

from validation.models import Phrase, LanguageVariant


class Command(BaseCommand):
    help = "looks for the combined ˆ+[aeio] character and replaces it with the single ê character (but the correct vowel)"

    def handle(self, *args, **options) -> None:
        phrases = Phrase.objects.all()
        language = LanguageVariant.objects.get(code="moswacihk")
        for phrase in phrases:
            if phrase.language == language:
                if phrase.transcription.find("ê"):
                    phrase.transcription = phrase.transcription.replace("ê", "ê")
                if phrase.transcription.find("â"):
                    phrase.transcription = phrase.transcription.replace("â", "â")
                if phrase.transcription.find("î"):
                    phrase.transcription = phrase.transcription.replace("î", "î")
                if phrase.transcription.find("ô"):
                    phrase.transcription = phrase.transcription.replace("ô", "ô")
            phrase.save()
