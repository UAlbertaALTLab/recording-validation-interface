from django.core.management.base import BaseCommand

from validation.models import Phrase, LanguageVariant, Issue, Speaker


class Command(BaseCommand):
    help = "Determines if the phrase is already in the Maskwacîs dictionary"

    def handle(self, *args, **options):
        phrases = Phrase.objects.all()
        language, _ = LanguageVariant.objects.get_or_create(
            name="Maskwacîs", code="maskwacis"
        )
        for phrase in phrases:
            if not phrase.language:
                phrase.language = language
                phrase.save()

        issues = Issue.objects.all()
        for issue in issues:
            issue.language = language
            issue.save()

        speakers = Speaker.objects.all()
        for speaker in speakers:
            speaker.languages.add(language)
