from os import fspath

import divvunspell
from difflib import Differ, SequenceMatcher, get_close_matches
import operator

import requests
import json

from django.conf import settings

"""
RULES

    adding/removing diacritics or hyphens, swapping glides w/y, or 
    adding/removing aspirations -h- between vowel and consonant would have a weight of zero.
    inserting the vowel -i- between two consonants would have a half-weight (0.5).
    inserting/removing/swapping any other characters would have a normal weight of one.

"""


archive = divvunspell.SpellerArchive(fspath(settings.BASE_DIR / 'crk.zhfst'))
speller = archive.speller()

vowels = ["a", "i", "o", "â", "î", "ô"]
consonants = ["  c", "  h", "  k", "  m", "  n", "  p", "  s", "  t", "  w", "  y"]


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


def get_differ(word, suggestion):
    med = 0
    dif = Differ()
    df = list(dif.compare(word, suggestion))
    for i in range(len(df)):
        c = df[i]

        # check for replaced e with ê
        # we should never replace ê with e though
        if c == "- e":
            if i + 1 < len(df):
                if df[i + 1] == "+ ê":
                    continue

        if c == "+ ê":
            if i - 1 >= 0:
                if df[i - 1] == "- e":
                    continue

        # no change, carry on
        if "+" not in c and "-" not in c:
            continue

        # added or removed a hyphen
        if c == "- -" or c == "+ -":
            continue

        # check for swapping glides
        if c == "- y":
            if i + 1 < len(df):
                if df[i + 1] == "+ w":
                    continue

        if c == "- w":
            if i + 1 < len(df):
                if df[i + 1] == "+ y":
                    continue

        if c == "+ y":
            if i - 1 >= 0:
                if df[i - 1] == "- w":
                    continue

        if c == "+ w":
            if i - 1 >= 0:
                if df[i - 1] == "- y":
                    continue

        # end check for swapping glides

        if c.split()[1] in vowels:
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
    url = "https://sapir.artsrn.ualberta.ca/cree-dictionary/click-in-text/?q=" + word
    r = requests.get(url, verify=False)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        return "Error getting request"


def get_distance_with_translations(word):
    suggestions = get_edit_distance(word)
    for word in suggestions:
        r = get_translations_from_itwewina(word)
        defs = []
        analysis = ""
        for i in r["results"]:
            if type(i["definitions"]) == list:
                defs.append(i["definitions"])
            analysis = i["lemma_wordform"]["analysis"]

        translations = []
        for d in defs:
            for i in d:
                if type(i) == dict and i["text"]:
                    translations.append(i["text"])

        suggestions[word] = {
            "med": suggestions[word],
            "translation": translations,
            "analysis": analysis,
        }

    return suggestions


if __name__ == "__main__":
    word = "ekwa"
    print(get_distance_with_translations(word))
