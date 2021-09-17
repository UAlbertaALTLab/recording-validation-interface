from django.core.management.base import BaseCommand

from validation.models import Phrase, Dialect, Issue, Speaker


class Command(BaseCommand):
    help = "Determines if the phrase is already in the Maskwacîs dictionary"

    def handle(self, *args, **options):
        phrases = Phrase.objects.all()
        dialect = Dialect.objects.get(code="maskwacis")
        for phrase in phrases:
            if not phrase.dialect:
                phrase.dialect = dialect
                phrase.save()

        issues = Issue.objects.all()
        for issue in issues:
            issue.dialect = dialect
            issue.save()

        speakers = Speaker.objects.all()
        for speaker in speakers:
            speaker.dialects.add(dialect)
