from django.core.management.base import BaseCommand  # type: ignore

from validation.models import Phrase, LanguageVariant
from tqdm import tqdm


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
        for phrase in tqdm(phrases):
            ascii_phrase = phrase.transcription.encode("ascii", "replace")
            i = 0  # index in string
            new_phrase = ""
            for c in ascii_phrase:
                char = phrase.transcription[i]
                if c == "63":
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
                        new_phrase += char
                else:
                    new_phrase += char
                i += 1
            phrase.transcription = new_phrase
            phrase.save()
