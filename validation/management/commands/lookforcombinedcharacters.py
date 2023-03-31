from django.core.management.base import BaseCommand  # type: ignore

from validation.models import Phrase, LanguageVariant


class Command(BaseCommand):
    help = "looks for the combined ˆ+[aeio] character and replaces it with the single ê character (but the correct vowel)"

    def handle(self, *args, **options) -> None:
        """
        For some reason, the system recognizes the dual character î as the same thing as the
        single character î, even when they're different. It's infuriating and I've spent a long time
        trying to fix this error.
        So, we can compare them as the same, but we need to turn the string into an ascii object first
        We know we have a special character if it gets ascii encoded as '?', or ascii value 63
        We store the indices of all the 63's, then construct a new string where we replace
        these dual character special characters with the single character equivalent. Actually, we just
        replace all the special characters with their equivalent.
        It's convoluted, but it should work.
        """
        language = LanguageVariant.objects.get(code="moswacihk")
        phrases = Phrase.objects.filter(language=language)
        for phrase in phrases:
            ascii_phrase = phrase.transcription.encode("ascii", "replace")
            i = 0  # index in string
            indices_to_replace = []
            for c in ascii_phrase:
                if c == "63":
                    indices_to_replace.append(i)
                i += 1
            j = 0
            new_phrase = ""
            while j < len(phrase.transcription):
                if j in indices_to_replace:
                    char = phrase.transcription[j]
                    if char == "ê":
                        new_phrase += "ê"
                    elif char == "â":
                        new_phrase += "â"
                    elif char == "î":
                        new_phrase += "î"
                    elif char == "ô":
                        new_phrase += "ô"
                    else:
                        # maybe we actually have a '?'
                        new_phrase += phrase.transcription[j]
                else:
                    new_phrase += phrase.transcription[j]
                j += 1

            phrase.save()
