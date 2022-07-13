#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright (C) 2018 Eddie Antonio Santos <easantos@ualberta.ca>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import unicodedata
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from librecval.normalization import normalize_sro, to_indexable_form, normalize_phrase
from librecval.recording_session import Location, SessionID, TimeOfDay

User = get_user_model()


def choices_from_enum(enum_class):
    """
    Utility for converting a Python 3.4+ Enum into a choices for a Django
    model. Retuns a dictionary suitable for using as keyword arguments for a
    CharField.
    """
    choices = tuple((x.value, x.value) for x in enum_class)
    max_length = max(len(x.value) for x in enum_class)
    return dict(max_length=max_length, choices=choices)


def arguments_for_choices(choices):
    """
    Given a sequence of choices, generates the appropriate keyword arguments
    for a CharField.
    """
    return dict(choices=choices, max_length=max(len(choice[0]) for choice in choices))


class LanguageVariant(models.Model):
    name = models.CharField(
        help_text="The full name of the language", blank=False, max_length=256
    )

    code = models.CharField(
        help_text="A url-safe identifier for this language",
        blank=False,
        max_length=16,
    )

    description = models.CharField(
        help_text="A short description of this language/where it is spoken",
        null=True,
        max_length=1024,
    )

    language_family = models.CharField(
        help_text="The larger language family that this variant belongs to, if any",
        null=True,
        blank=True,
        max_length=256,
    )

    endonym = models.CharField(
        help_text="The name of the language in the language itself",
        null=True,
        blank=True,
        max_length=256,
    )

    def __str__(self) -> str:
        return self.name


class SemanticClass(models.Model):
    """
    A semantic class, typically from WordNet or RapidWords that describes a phrase
    """

    MAX_TRANSCRIPTION_LENGTH = 256

    META = "metadata"
    MANUAL = "manual classification"
    ELICIT = "elicitation sheet"
    SOURCE_CHOICES = (
        (META, "Metadata"),
        (MANUAL, "Manual Classification"),
        (ELICIT, "Elicitation Sheet"),
    )

    # Origin values
    RW = "rapidwords"
    WN = "wordnet"
    O = "other"

    ORIGIN_CHOICES = (
        (RW, "RapidWords"),
        (WN, "WordNet"),
        (O, "Other"),
    )

    source = models.CharField(
        help_text="How did we determine this class?",
        blank=True,
        **arguments_for_choices(SOURCE_CHOICES),
    )

    origin = models.CharField(
        help_text="Where did this class come from?",
        blank=True,
        **arguments_for_choices(ORIGIN_CHOICES),
    )

    classification = models.CharField(
        help_text="The classification for this semantic class",
        blank=True,
        max_length=256,
    )

    hypernyms = models.ManyToManyField("self", blank=True, default=None)
    hyponyms = models.ManyToManyField("self", blank=True, default=None)

    language_variants = models.ManyToManyField(
        LanguageVariant, blank=True, default=None
    )

    # Keep track of Semantic Class' history, so we can review, revert, and inspect them.
    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.classification


class Phrase(models.Model):
    """
    A recorded phrase. A phrase may either be a word or a sentence with at
    least one recording. Phrases may be awaiting validation, or may have
    already be validated.
    """

    MAX_TRANSCRIPTION_LENGTH = 256

    WORD = "word"
    SENTENCE = "sentence"
    KIND_CHOICES = ((WORD, "Word"), (SENTENCE, "Sentence"))

    # Status values
    NEW = "new"
    AUTO = "auto-standardized"
    STANDARDIZED = "standardized"
    LINKED = "linked"
    VALIDATED = "validated"
    REVIEW = "needs review"
    USER = "user-submitted"

    STATUS_CHOICES = (
        (NEW, "New"),
        (AUTO, "Auto-standardized"),
        (STANDARDIZED, "Standardized"),
        (LINKED, "Linked"),
        (VALIDATED, "Validated"),
        (REVIEW, "Needs review"),
        (USER, "User-submitted"),
    )

    MASKWACÎS_DICTIONARY = "MD"
    ONESPOT_SAPIR = "OS"
    TVPD = "TVPD"
    PFN = "PFN"
    I3 = "I3"
    AUTO = "AUTO"
    NEW_WORD = "new"
    ORIGIN_CHOICES = (
        (MASKWACÎS_DICTIONARY, "Maskwacîs Dictionary"),
        (ONESPOT_SAPIR, "Onespot-Sapir Dictionary"),
        (TVPD, "Tsuut'ina Verb Phrase Dictionary"),
        (PFN, "Paul First Nation"),
        (I3, "Îethka Îabi Institude"),
        (AUTO, "Auto-synthesized speech"),
        (NEW_WORD, "New word"),
    )

    field_transcription = models.CharField(
        help_text="The transcription from the day of the recording. This should never change.",
        blank=False,
        max_length=MAX_TRANSCRIPTION_LENGTH,
    )

    transcription = models.CharField(
        help_text="The validated transciption of the target language phrase.",
        blank=False,
        max_length=MAX_TRANSCRIPTION_LENGTH,
    )

    translation = models.CharField(
        help_text="The English translation of the phrase.",
        blank=False,
        max_length=MAX_TRANSCRIPTION_LENGTH,
    )
    kind = models.CharField(
        help_text="Is this phrase a word or a sentence?",
        blank=False,
        **arguments_for_choices(KIND_CHOICES),
    )
    validated = models.BooleanField(
        help_text="Has this phrase be validated?", default=False
    )

    language = models.ForeignKey(
        LanguageVariant,
        help_text="The language this phrase belongs to",
        on_delete=models.PROTECT,
        null=True,
    )

    semantic_class = models.ManyToManyField(SemanticClass, blank=True)

    status = models.CharField(
        help_text="Status in the validation process",
        blank=False,
        default=NEW,
        **arguments_for_choices(STATUS_CHOICES),
    )

    origin = models.CharField(
        help_text="How did we get this phrase?",
        null=True,
        default=NEW_WORD,
        **arguments_for_choices(ORIGIN_CHOICES),
    )

    osid = models.CharField(
        help_text="Typically, this is the os##### for Tsuut'ina recordings",
        null=True,
        max_length=16,
    )

    # A hidden field that will be indexed to make fuzzy matching easier.
    fuzzy_transcription = models.CharField(
        help_text="The indexed form of the transcription to facilitate "
        "fuzzy matching (automatically managed).",
        null=False,
        blank=False,
        max_length=MAX_TRANSCRIPTION_LENGTH,
        editable=False,
        # Nothing in the database should have this form.
        default="<UNINDEXABLE>",
    )

    date = models.DateField(
        help_text="When was this phrase last modified?", auto_now_add=True
    )

    analysis = models.CharField(
        help_text="The analysis of the phrase", blank=True, max_length=256
    )

    modifier = models.CharField(
        help_text="The person who added or modified the phrase",
        default="AUTO",
        max_length=64,
    )

    comment = models.CharField(
        help_text="Comments about the phrase",
        blank=True,
        null=True,
        max_length=2048,
    )

    # Keep track of Phrases' history, so we can review, revert, and inspect them.
    history = HistoricalRecords()

    class Meta:
        indexes = [
            # An index to support O(log n) matches on FUZZY transcriptions.
            # To search, query on fuzzy_transcriptions, and use
            # librecval.normalization.to_indexable_form() on the query.
            models.Index(
                fields=("fuzzy_transcription",), name="fuzzy_transcription_idx"
            ),
            # DEPRECATED: Allow for rapid look-up on the transcription
            models.Index(fields=("transcription",), name="transcription_idx"),
        ]

    @property
    def recordings(self):
        """
        A query set of the current recordings.
        """
        return self.recording_set.all()

    def clean(self):
        """
        Cleans the text fields.
        """
        self.field_transcription = normalize_phrase(self.field_transcription)
        self.transcription = normalize_phrase(self.transcription)

        if not self.kind:
            self.kind = self.SENTENCE if " " in self.transcription else self.WORD

        if self.kind == self.WORD:
            self.transcription = normalize_sro(self.transcription)

    def save(self, *args, **kwargs):
        # Make sure the fuzzy match is always up to date
        self.fuzzy_transcription = to_indexable_form(self.transcription)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.transcription


class Speaker(models.Model):
    """
    A person who spoke at the recording sessions.
    """

    # We store gender so that we can categorize how their voice sounds.
    # The community is interested in hearing each word with both a male and a
    # female voice.
    # Although I believe gender is a spectrum (and can even be null!),
    # we personally know all of the speakers, and they all identifiy as either
    # male or female.
    MALE = "M"
    FEMALE = "F"
    GENDER_CHOICES = ((MALE, "Male"), (FEMALE, "Female"))

    code = models.CharField(
        help_text="Short code assigned to speaker in the ellicitation metadata.",
        max_length=8,
        primary_key=True,
    )
    # Initially, gender and full name in the database will be imported as
    # None/null, but they should ultimately be set manually.
    full_name = models.CharField(help_text="The speaker's full name.", max_length=128)
    gender = models.CharField(
        help_text="Gender of the voice.",
        max_length=1,
        choices=GENDER_CHOICES,
        null=True,
    )

    user = models.ForeignKey(
        User,
        help_text="The User object associated with this Speaker, if any",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    languages = models.ManyToManyField(LanguageVariant, blank=True)

    target_bio_text = models.CharField(
        help_text="The English transcription of the speaker bio",
        null=True,
        blank=True,
        max_length=4096,
    )
    source_bio_text = models.CharField(
        help_text="The Cree transcription of the speaker bio",
        null=True,
        blank=True,
        max_length=4096,
    )

    target_bio_audio = models.FileField(
        # relative to settings.MEDIA_ROOT
        upload_to=settings.RECVAL_AUDIO_PREFIX,
        blank=True,
    )
    source_bio_audio = models.FileField(
        # relative to settings.MEDIA_ROOT
        upload_to=settings.RECVAL_AUDIO_PREFIX,
        blank=True,
    )

    @property
    def language(self):
        """
        Which language this person speaks.
        """
        # Hard-coded for now, but it makes implementing this field trival.
        return [
            language.name
            for language in LanguageVariant.objects.all()
            if language in self.languages.all()
        ]

    @property
    def anonymous(self):
        """
        TODO: implement this attribute
        """
        # XXX: For now, all speakers are NOT anonymous.
        return False

    def clean(self):
        self.code = self.code.strip().upper()
        if not re.match(r"\A[A-Z]+[0-9]?\Z", self.code):
            raise ValidationError(
                _(
                    "Speaker code must be a single all-caps word, "
                    "optionally followed by a digit"
                )
            )

    def get_absolute_url(self) -> str:
        """
        Returns a URL for where to find the speaker bio.
        """
        if self.language:
            lang_code = LanguageVariant.objects.get(name=self.language[0]).code
            return f"https://speech-db.altlab.app/{lang_code}/speakers/{self.code}"
        else:
            return "https://speech-db.altlab.app/maskwacis/speakers/"

    def __str__(self):
        return self.code


class RecordingSession(models.Model):
    """
    A session during which a number of recordings were made.

    Example sessions:

    2017-11-01-AM-OFF-_:
        Happened on the morning of November 1, 2017 in the office.
    """

    id = models.CharField(primary_key=True, max_length=len("2000-01-01-__-___-_"))

    date = models.DateField(help_text="The day the session occured.")
    # See librecval for the appropriate choices:
    time_of_day = models.CharField(
        help_text="The time of day the session occured. May be empty.",
        blank=True,
        default="",
        **choices_from_enum(TimeOfDay),
    )
    location = models.CharField(
        help_text="The location of the recordings. May be empty.",
        blank=True,
        default="",
        **choices_from_enum(Location),
    )
    subsession = models.IntegerField(
        help_text="The 'subsession' number, if applicable.", null=True, blank=True
    )

    def as_session_id(self) -> str:
        """
        Converts back into a SessionID object.
        """
        return SessionID(
            date=self.date,
            time_of_day=parse_or_none(TimeOfDay, self.time_of_day),
            location=parse_or_none(Location, self.location),
            subsession=self.subsession,
        )

    @classmethod
    def create_from(cls, session_id):
        """
        Create the model from the internal data class.
        """
        return cls(
            id=str(session_id),
            date=session_id.date,
            time_of_day=enum_value_or_blank(session_id.time_of_day),
            location=enum_value_or_blank(session_id.location),
            subsession=session_id.subsession,
        )

    @classmethod
    def objects_by_id(cls, session_id: SessionID):
        """
        Fetch a RecordingSession by its Session ID.
        """
        return cls.objects.filter(id=str(session_id))

    @classmethod
    def get_or_create_by_session_id(cls, session_id: SessionID):
        """
        Same as cls.objects.get_or_create(), but only deals with session IDs.
        """
        try:
            (obj,) = cls.objects_by_id(session_id)
        except ValueError:
            obj = cls.create_from(session_id)
            obj.save()
            return obj, True
        else:
            return obj, False

    def __str__(self):
        return str(self.as_session_id())


@receiver(pre_save, sender=RecordingSession)
def generate_primary_key(sender, instance, **kwargs):
    """
    When a recording session gets saved this sets the primary
    key to the session id, e.g. 2017-11-01-AM-OFF-_
    This happens automatically on save
    """
    instance.id = str(instance.as_session_id())


# The length of a SHA 256 hash, as hexadecimal characters.
SHA256_HEX_LENGTH = 64


class Recording(models.Model):
    """
    A recording of a phrase.
    """

    GOOD = "good"
    BAD = "bad"
    UNKNOWN = "unknown"

    QUALITY_CHOICES = [(GOOD, "Good"), (BAD, "Bad"), (UNKNOWN, "Unknown")]

    id = models.CharField(primary_key=True, max_length=SHA256_HEX_LENGTH)

    compressed_audio = models.FileField(
        # relative to settings.MEDIA_ROOT
        upload_to=settings.RECVAL_AUDIO_PREFIX,
    )

    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE)
    timestamp = models.IntegerField(
        help_text="The offset (in milliseconds) when the phrase starts in the master file"
    )
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE)
    session = models.ForeignKey(RecordingSession, on_delete=models.CASCADE, null=True)

    quality = models.CharField(
        help_text="Is the recording clean? Is it suitable to use publicly?",
        max_length=64,
        blank=True,
        choices=QUALITY_CHOICES,
    )

    is_best = models.BooleanField(
        help_text="Is this the best recording of the bunch?", default=False
    )

    comment = models.CharField(
        help_text="The comment provided in the ELAN file",
        max_length=256,
        blank=True,
    )

    wrong_word = models.BooleanField(
        help_text="This recording has the wrong word", default=False
    )

    wrong_speaker = models.BooleanField(
        help_text="This recording has the wrong speaker", default=False
    )

    is_user_submitted = models.BooleanField(
        help_text="This recording was submitted online by a user", default=False
    )

    was_user_submitted = models.BooleanField(
        help_text="This recording was submitted online by a user, but is now approved for use",
        default=False,
        blank=True,
    )

    # Keep track of the recording's history.
    history = HistoricalRecords(excluded_fields=["compressed_audio"])

    def __str__(self):
        return f'"{self.phrase}" recorded by {self.speaker} during {self.session}'

    def get_absolute_url(self) -> str:
        """
        Return a URL to the compressed audio file.
        Note: you will still need to call HttpRequest.build_absolute_uri() to get an
        absolute URI (i.e., with scheme and hostname).
        """
        return self.compressed_audio.url

    def as_json(self, request):
        """
        Returns JSON that API clients expect for a single recording.
        """
        return {
            "wordform": self.phrase.transcription,
            "speaker": self.speaker.code,
            "speaker_name": self.speaker.full_name,
            "anonymous": self.speaker.anonymous,
            "gender": self.speaker.gender,
            "language": self.speaker.language,
            "recording_url": request.build_absolute_uri(self.get_absolute_url()),
            "speaker_bio_url": request.build_absolute_uri(
                self.speaker.get_absolute_url()
            ),
            "is_best": self.is_best,
        }

    @staticmethod
    def get_path_to_audio_directory() -> Path:
        """
        Returns the path to where compressed audio should be written to.
        """
        return Path(settings.MEDIA_ROOT) / settings.RECVAL_AUDIO_PREFIX


class Issue(models.Model):
    comment = models.CharField(
        help_text="The comment left by the validator",
        blank=True,
        max_length=1024,
    )

    source_language_suggestion = models.CharField(
        help_text="The Target Language spelling suggestion from the validator",
        blank=True,
        max_length=1024,
    )

    target_language_suggestion = models.CharField(
        help_text="The Source Language spelling suggestion from the validator",
        blank=True,
        max_length=1024,
    )

    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE, blank=True, null=True)

    recording = models.ForeignKey(
        Recording, on_delete=models.CASCADE, blank=True, null=True
    )

    language = models.ForeignKey(
        LanguageVariant,
        help_text="The language this phrase belongs to",
        on_delete=models.PROTECT,
        null=True,
    )

    created_by = models.CharField(
        help_text="The person who filed this issue",
        default="",
        max_length=64,
    )

    created_on = models.DateField(
        help_text="When was this issue filed?",
    )

    RESOLVED = "resolved"
    OPEN = "open"
    STATUS_CHOICES = [(RESOLVED, "Resolved"), (OPEN, "Open")]

    status = models.CharField(
        help_text="The status of the issue",
        max_length=64,
        choices=STATUS_CHOICES,
        default=OPEN,
    )


# ############################### Utilities ############################### #


def enum_value_or_blank(enum) -> str:
    """
    Returns either the value of the enumerated property, or blank (the empty string).
    """
    # `and` prevents accessing attributes on a None value.
    return (enum and enum.value) or ""


def parse_or_none(cls, value):
    """
    Given a value from a db.CharField(choices=...) field, returns the parsed
    value according to the enumeration or None.

    Is it just me, or is it getting monadic in here?
    """
    # `and` prevents calling .parse() on a None value.
    return (value and cls.parse(value)) or None
