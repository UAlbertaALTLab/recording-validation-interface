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
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from librecval.normalization import normalize_sro, to_indexable_form
from librecval.recording_session import Location, SessionID, TimeOfDay


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


class Phrase(models.Model):
    """
    A recorded phrase. A phrase may either be a word or a sentence with at
    least one recording. Phrases may be awaiting validation, or may have
    already be validated.
    """

    # The only characters allowed in the transcription are the Cree SRO
    # alphabet (in circumflexes), and some selected punctuation.
    ALLOWED_TRANSCRIPTION_CHARACTERS = set("ptkcshmn yw rl êiîoôaâ -")

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

    STATUS_CHOICES = (
        (NEW, "New"),
        (AUTO, "Auto-standardized"),
        (STANDARDIZED, "Standardized"),
        (LINKED, "Linked"),
        (VALIDATED, "Validated"),
        (REVIEW, "Needs review"),
    )

    MASKWACÎS_DICTIONARY = "MD"
    NEW_WORD = "new"
    ORIGIN_CHOICES = (
        (MASKWACÎS_DICTIONARY, "Maskwacîs Dictionary"),
        (NEW_WORD, "New word"),
    )

    field_transcription = models.CharField(
        help_text="The transcription from the day of the recording. This should never change.",
        blank=False,
        max_length=MAX_TRANSCRIPTION_LENGTH,
    )

    transcription = models.CharField(
        help_text="The validated transciption of the Cree phrase.",
        blank=False,
        max_length=MAX_TRANSCRIPTION_LENGTH,
    )

    translation = models.CharField(
        help_text="The English translation of the phrase.", blank=False, max_length=256
    )
    kind = models.CharField(
        help_text="Is this phrase a word or a sentence?",
        blank=False,
        **arguments_for_choices(KIND_CHOICES),
    )
    validated = models.BooleanField(
        help_text="Has this phrase be validated?", default=False
    )

    status = models.CharField(
        help_text="Status in the validation process",
        blank=False,
        default=NEW,
        **arguments_for_choices(STATUS_CHOICES),
    )
    # TODO: during the import process, try to determine automatically whether
    # the word came from the Maswkacîs dictionary.
    origin = models.CharField(
        help_text="How did we get this phrase?",
        null=True,
        default=NEW_WORD,
        **arguments_for_choices(ORIGIN_CHOICES),
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
        help_text="The analysis of the Cree phrase", blank=True, max_length=256
    )

    modifier = models.CharField(
        help_text="The person who added or modified the phrase",
        default="AUTO",
        max_length=64,
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
        self.field_transcription = unicodedata.normalize(
            "NFC", self.field_transcription
        )

        self.transcription = normalize_sro(self.transcription)
        assert self.ALLOWED_TRANSCRIPTION_CHARACTERS.issuperset(self.transcription)

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

    @property
    def dialect(self):
        """
        Which dialect this person speaks.
        """
        # Hard-coded for now, but it makes implementing this field trival.
        return "Maskwacîs"

    @property
    def anonymous(self):
        """
        TODO: implement this attribute
        """
        # XXX: For now, all speakers are NOT anonymous.
        return False

    # TODO: add field for speaker bio (en)
    # TODO: add field for speaker bio (crk)

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
        # TODO: Change this when implementing:
        # https://github.com/UAlbertaALTLab/recording-validation-interface/issues/72
        return f"https://www.altlab.dev/maskwacis/Speakers/{self.code}.html"

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


class PresentableRecordingModelManager(models.Manager):
    """
    Returns Recording instances only for recordings we think are
    clean/usable to be presented to users of e.g., the dictionary.
    """

    def get_queryset(self) -> "QuerySet[Recording]":
        recordings = super().get_queryset()
        return (
            recordings.exclude(quality=Recording.BAD)
            .exclude(wrong_word=True)
            .exclude(wrong_speaker=True)
            # We use the "gender" field as a proxy to see whether a speaker's data has
            # been properly filled out: exclude speakers whose gender field has not been
            # input. An admin must put *something* in the gender field before the
            # speaker shows up in API results.
            .exclude(speaker__gender__isnull=True)
        )


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
    session = models.ForeignKey(RecordingSession, on_delete=models.CASCADE)

    # TODO: determine this automatically during import process
    quality = models.CharField(
        help_text="Is the recording clean? Is it suitable to use publicly?",
        max_length=64,
        blank=True,
        choices=QUALITY_CHOICES,
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

    # Keep track of the recording's history.
    history = HistoricalRecords(excluded_fields=["compressed_audio"])

    # Default Django model manager:
    objects = models.Manager()
    # Custom model manager that returns only recordings that are okay to present:
    presentable_objects = PresentableRecordingModelManager()

    def __str__(self):
        return f'"{self.phrase}" recorded by {self.speaker} during {self.session}'

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

    suggested_cree = models.CharField(
        help_text="The Cree spelling suggested by the validator",
        blank=True,
        max_length=1024,
    )

    suggested_english = models.CharField(
        help_text="The English spelling suggested by the validator",
        blank=True,
        max_length=1024,
    )

    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE, blank=True, null=True)

    recording = models.ForeignKey(
        Recording, on_delete=models.CASCADE, blank=True, null=True
    )

    created_by = models.CharField(
        help_text="The person who filed this issue",
        default="",
        max_length=64,
    )

    created_on = models.DateField(
        help_text="When was this issue filed?",
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
