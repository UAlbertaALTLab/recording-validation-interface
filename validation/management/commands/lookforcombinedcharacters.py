from django.core.management.base import BaseCommand  # type: ignore

from validation.models import Phrase, LanguageVariant
from tqdm import tqdm


class Command(BaseCommand):
    help = "looks for the combined ˆ+[aeio] character and replaces it with the single ê character (but the correct vowel)"

    def handle(self, *args, **options) -> None:
        """
        Many of the characters are combined characters, ˆ+e instead of ê. We need them to be one character
        instead of 2. So, we convert the string to unicode, which represents the joining ˆ as \xcc\x82.
        We replace those characters with the correct single character, which appears as the character before
        the \xcc\x82. That is, the combined "ahâm" is represented as "'aha\\xcc\\x82m'", so we replace the
        "a\\xcc\\x82" with "â"
        """
        language = LanguageVariant.objects.get(code="moswacihk")
        phrases = Phrase.objects.filter(language=language)
        for phrase in tqdm(phrases):
            unicode_phrase = repr(phrase.transcription)
            i = 0  # index in unicode_phrase
            j = 0  # index in phrase.transcription
            new_phrase = ""
            while i < len(unicode_phrase) and j < len(phrase.transcription):
                c = unicode_phrase[i]
                if c == "'":
                    i += 1
                else:
                    char = phrase.transcription[j]
                    j += 1
                    if (i + 1) < len(unicode_phrase):
                        next_char = unicode_phrase[i + 1]
                        if next_char == "\\":
                            if c == "e":
                                new_phrase += "ê"
                            elif c == "a":
                                new_phrase += "â"
                            elif c == "i":
                                new_phrase += "î"
                            elif c == "o":
                                new_phrase += "ô"
                            # the next char is \
                            # the sequence we're looking at it \xcc\x82
                            # we want to jump the rest of this sequence
                            # so we increase by 9 to get to the next character
                            i += 9
                        else:
                            # the next character isn't the special character
                            new_phrase += char
                            i += 1
                    else:
                        # don't forget the last character!
                        new_phrase += char
                        i += 1
            phrase.transcription = new_phrase
            phrase.save()
