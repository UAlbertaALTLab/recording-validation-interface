from os import fspath

import divvunspell
from difflib import Differ, SequenceMatcher, get_close_matches
from urllib.parse import urljoin
import operator

import requests
import json

from django.conf import settings
from django.utils.http import urlencode

"""
RULES

    adding/removing diacritics or hyphens, swapping glides w/y, or 
    adding/removing aspirations -h- between vowel and consonant would have a weight of zero.
    inserting the vowel -i- between two consonants would have a half-weight (0.5).
    inserting/removing/swapping any other characters would have a normal weight of one.

"""


archive = divvunspell.SpellerArchive(fspath(settings.BASE_DIR / "crk.zhfst"))
speller = archive.speller()

vowels = ["a", "i", "o", "â", "î", "ô", "e", "ê"]
consonants = [f"  {char}" for char in "chkmnpstwy"]


def get_edit_distance(word):

    ranked_suggestions = speller.suggest(word)
    suggestions = [s[0] for s in ranked_suggestions]

    rankings = {}
    for s in suggestions:
        med = get_differ(word, s)
        rankings[s] = med

    sorted_tuples = sorted(rankings.items(), key=operator.itemgetter(1))
    sorted_rankings = {k: v for k, v in sorted_tuples}

    return sorted_rankings


def has_vowel(c):
    """
    Returns True if the split string contains a vowel
    and the vowel was either added or removed from the original word
    to create the suggestion (hence the "split")
    """
    return len(c.split()) > 1 and c.split()[1] in vowels


def get_differ(word, suggestion):
    med = 0
    df = list(Differ().compare(word, suggestion))

    def diff_char_or_none(index):
        if index >= 0 and index < len(df):
            return df[index]
        return None

    for i in range(len(df)):
        c = df[i]

        # check for replaced e with ê
        # we should never replace ê with e though
        if c == "- e" and diff_char_or_none(i + 1) == "+ ê":
            continue

        if c == "+ ê" and diff_char_or_none(i - 1) == "- e":
            continue

        # no change, carry on
        if "+" not in c and "-" not in c:
            continue

        # added or removed a hyphen
        if c == "- -" or c == "+ -":
            continue

        # check for swapping glides
        if c == "- y" and diff_char_or_none(i + 1) == "+ w":
            continue

        if c == "- w" and diff_char_or_none(i + 1) == "+ y":
            continue

        if c == "+ y" and diff_char_or_none(i - 1) == "- w":
            continue

        if c == "+ w" and diff_char_or_none(i - 1) == "- y":
            continue

        # end check for swapping glides

        if has_vowel(c):
            # adding or removing a diacritic from a vowel has cost 0
            alt = get_analog(c)
            if i + 1 < len(df):
                if df[i + 1] == alt:
                    continue
            if i - 1 >= 0:
                if df[i - 1] == alt:
                    continue

        if "i" in c:
            # adding an -i- between two consonants has cost 0.5
            j = i + 1 if i + 1 < len(df) else None
            k = i - 1 if i - 1 >= 0 else None
            if j and k:
                if df[j] in consonants and df[k] in consonants:
                    med += 0.5
                    continue

        if "h" in c:
            # did we just add an -h- between a vowel and a consonant?
            j = i + 1 if i + 1 < len(df) else None
            k = i - 1 if i - 1 >= 0 else None
            if j and k:
                after = df[j].replace("-", "")
                after = after.replace("+", "")
                before = df[k].replace("-", "")
                before = before.replace("+", "")
                after = "  " + after.strip()
                before = before.strip()

                if after in consonants and before in vowels:
                    # we did, this costs nothing
                    continue

        # everything else has cost 1
        med += 1

    return med


def get_analog(char):
    # take in '- vowel'
    # return '+ vowel with hat'
    # OR
    # take in '+ vowel'
    # return '- vowel with hat'

    alt = ""
    if "-" in char:
        alt = char.replace("-", "+")
    else:
        alt = char.replace("+", "-")

    if char.split()[1] in ["a", "i", "o"]:
        alt = alt.replace("a", "â")
        alt = alt.replace("i", "î")
        alt = alt.replace("o", "ô")

    elif char.split()[1] in ["â", "î", "ô"]:
        alt = alt.replace("â", "a")
        alt = alt.replace("î", "i")
        alt = alt.replace("ô", "o")

    return alt


def get_translations_from_itwewina(word):
    url = (
        urljoin(settings.ITWEWINA_URL, "click-in-text/") + "?" + urlencode({"q": word})
    )
    r = requests.get(url)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        return "Error getting request"


def get_translations(results):
    matches = []

    for i in results["results"]:
        translations, analysis = extract_translations(i["lemma_wordform"])
        if {"translations": translations, "analysis": analysis} not in matches:
            matches.append({"translations": translations, "analysis": analysis})

    return matches


def extract_translations(entry):
    translations = []

    if type(entry["definitions"]) == list and len(entry["definitions"]) > 0:
        translations = [str(j["text"]) for j in entry["definitions"]]

    translations = "; ".join(translations)
    analysis = entry["analysis"]

    return translations, analysis


def get_distance_with_translations(word):
    suggestions = get_edit_distance(word)
    for word in suggestions:
        results = get_translations_from_itwewina(word)

        matches = get_translations(results)

        suggestions[word] = {
            "med": suggestions[word],
            "matches": matches,
            "len": len(matches) if len(matches) == 1 else len(matches) + 1,
        }

    return suggestions


def perfect_match(word, suggestions):
    match = None
    for suggestion in suggestions:
        if suggestions[suggestion]["med"] == 0 or suggestion == word:
            if match is None:
                match = suggestions[suggestion]
            else:
                return None

    return match


def exactly_one_analysis(suggestion):
    analysis = ""
    if not suggestion:
        return False

    for wordform in suggestion["matches"]:
        if analysis == "":
            analysis = wordform["analysis"]
        if wordform["analysis"] != analysis:
            return False
    if analysis == "":
        return False
    return True
