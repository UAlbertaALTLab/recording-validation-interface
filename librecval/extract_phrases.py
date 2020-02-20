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


# Derived from Praat scripts written by Timothy Mills
#  - extract_items.praat
#  - extract_sessions.praat

import logging
import re
from decimal import Decimal
from hashlib import sha256
from os import fspath
from pathlib import Path
from typing import Dict, NamedTuple, Optional

import logme  # type: ignore
from librecval.normalization import normalize
from librecval.recording_session import SessionID, SessionMetadata
from pydub import AudioSegment  # type: ignore
from textgrid import IntervalTier, TextGrid  # type: ignore

# ############################### Exceptions ############################### #


class DuplicateSessionError(RuntimeError):
    """
    Raised when the session has already been found by another name.
    """


class MissingMetadataError(RuntimeError):
    """
    Raised when the cooresponding metadata cannot be found.
    """


class InvalidTextGridName(RuntimeError):
    """
    Raised when the TextGrid name does not follow an appropriate pattern.
    """


# ########################################################################## #


class RecordingInfo(NamedTuple):
    """
    All the information you could possible want to know about a recorded
    snippet.
    """

    session: SessionID
    speaker: str
    type: str
    timestamp: int  # in milliseconds
    transcription: str
    translation: str

    def signature(self) -> str:
        # TODO: make this resilient to changing type, transcription, and speaker.
        return (
            f"session: {self.session}\n"
            f"speaker: {self.speaker}\n"
            f"timestamp: {self.timestamp}\n"
            f"{self.type}: {self.transcription}\n"
            "\n"
            f"{self.translation}\n"
        )

    def compute_sha256hash(self) -> str:
        """
        Compute a hash that can be used as a ID for this recording.
        """
        return sha256(self.signature().encode("UTF-8")).hexdigest()


@logme.log
class RecordingExtractor:
    """
    Extracts recordings from a directory of sessions.
    """

    logger: logging.Logger

    def __init__(self, metadata=Dict[SessionID, SessionMetadata]) -> None:
        self.sessions: Dict[SessionID, Path] = {}
        self.metadata = metadata

    def scan(self, root_directory: Path):
        """
        Scans the directory provided for sessions.

        For each session directory found, its TextGrid/.wav file pairs are
        scanned for words and sentences.
        """
        self.logger.debug("Scanning %s for sessions...", root_directory)
        for session_dir in root_directory.iterdir():
            if not session_dir.resolve().is_dir():
                self.logger.debug("Rejecting %s; not a directory", session_dir)
                continue
            try:
                yield from self.extract_session(session_dir)
            except DuplicateSessionError:
                self.logger.exception("Skipping %s: duplicate", session_dir)
            except MissingMetadataError:
                self.logger.exception("Skipping %s: Missing metadata", session_dir)

    def extract_session(self, session_dir: Path):
        """
        Extracts recordings from a single session.
        """
        session_id = SessionID.from_name(session_dir.stem)
        if session_id in self.sessions:
            raise DuplicateSessionError(
                f"Duplicate session: {session_id} "
                f"found at {self.sessions[session_id]}"
            )
        if session_id not in self.metadata:
            raise MissingMetadataError(f"Missing metadata for {session_id}")

        self.logger.debug("Scanning %s for .TextGrid files", session_dir)
        text_grids = list(session_dir.glob("*.TextGrid"))
        self.logger.info("%d text grids in %s", len(text_grids), session_dir)

        for text_grid in text_grids:
            # Find the cooresponding audio with a couple different strategies.
            sound_file = find_audio_from_audacity_format(
                text_grid
            ) or find_audio_from_audition_format(text_grid)

            if sound_file is None:
                self.logger.warn("Could not find cooresponding audio for %s", text_grid)
                continue

            assert text_grid.exists() and sound_file.exists()
            self.logger.debug("Matching sound file for %s", text_grid)

            try:
                mic_id = get_mic_id(text_grid.stem)
            except InvalidTextGridName:
                if len(text_grids) != 1:
                    raise  # There's no way to determine the speaker.
                mic_id = 1
                self.logger.warn("Assuming single text grid is mic 1")

            speaker = self.metadata[session_id][mic_id]

            self.logger.debug(
                "Opening audio and text grid from %s for speaker %s",
                sound_file,
                speaker,
            )
            extractor = PhraseExtractor(
                session_id,
                AudioSegment.from_file(fspath(sound_file)),
                TextGrid.fromFile(fspath(text_grid)),
                speaker,
            )
            yield from extractor.extract_all()


@logme.log
def find_audio_from_audacity_format(text_grid: Path, logger=None) -> Optional[Path]:
    """
    Finds the associated audio in Audacity's format.
    """
    # TODO: tmill's kludge for certain missing filenames???
    sound_file = text_grid.with_suffix(".wav")
    logger.debug("[Audacity Format] Trying %s...", sound_file)
    return sound_file if sound_file.exists() else None


@logme.log
def find_audio_from_audition_format(text_grid: Path, logger=None) -> Optional[Path]:
    #  Gross code to try Adobe Audition recorded files
    session_dir = text_grid.parent

    # If it's in Audition format, there will be exactly ONE file with the
    # *.sesx extension.
    try:
        (audition_file,) = session_dir.glob("*.sesx")
    except ValueError:
        logger.debug("Could not find exactly one *.sesx file in %s", session_dir)
        return None

    sound_file = (
        session_dir / f"{audition_file.stem}_Recorded" / f"{text_grid.stem}.wav"
    )
    logger.debug("[Audition Format] Trying %s...", sound_file)
    return sound_file if sound_file.exists() else None


WORD_TIER_ENGLISH = 0
WORD_TIER_CREE = 1
SENTENCE_TIER_ENGLISH = 2
SENTENCE_TIER_CREE = 3


@logme.log
class PhraseExtractor:
    """
    Extracts recorings from a session directory.
    """

    logger: logging.Logger

    def __init__(
        self,
        session: SessionID,
        sound: AudioSegment,
        text_grid: TextGrid,
        speaker: str,  # Something like "ABC"
    ) -> None:
        self.session = session
        self.sound = sound
        self.text_grid = text_grid
        self.speaker = speaker

    def extract_all(self):
        assert len(self.text_grid.tiers) >= 4, "TextGrid has too few tiers"

        self.logger.debug("Extracting words from %s/%s", self.session, self.speaker)
        yield from self.extract_words(
            cree_tier=self.text_grid.tiers[WORD_TIER_CREE],
            english_tier=self.text_grid.tiers[WORD_TIER_ENGLISH],
        )

        self.logger.debug("Extracting sentences from %s/%s", self.session, self.speaker)
        yield from self.extract_sentences(
            cree_tier=self.text_grid.tiers[SENTENCE_TIER_CREE],
            english_tier=self.text_grid.tiers[SENTENCE_TIER_ENGLISH],
        )

    def extract_words(self, cree_tier, english_tier):
        yield from self.extract_phrases("word", cree_tier, english_tier)

    def extract_sentences(self, cree_tier, english_tier):
        yield from self.extract_phrases("sentence", cree_tier, english_tier)

    def extract_phrases(
        self, type_: str, cree_tier: IntervalTier, english_tier: IntervalTier
    ):
        assert is_cree_tier(cree_tier), cree_tier.name
        assert is_english_tier(english_tier), english_tier.name

        for interval in cree_tier:
            if not interval.mark or interval.mark.strip() == "":
                # This interval is empty, for some reason.
                continue

            transcription = normalize(interval.mark)

            start = to_milliseconds(interval.minTime)
            end = to_milliseconds(interval.maxTime)
            midtime = (interval.minTime + interval.maxTime) / 2

            # Figure out if this word belongs to a sentence.
            if type_ == "word" and self.timestamp_within_sentence(midtime):
                # It's an example sentence; leave it for the next loop.
                # TODO: WHY ARE WE SKIPPING IT AGAIN?
                self.logger.debug("%r is in a sentence", transcription)
                continue

            # Get the word's English gloss.
            english_interval = english_tier.intervalContaining(midtime)
            if english_interval is None:
                self.logger.warn("Could not find translation for %r", interval)
                continue

            translation = normalize(english_interval.mark)

            # Snip out the sounds.
            sound_bite = self.sound[start:end]
            # tmills: normalize sound levels (some speakers are very quiet)
            sound_bite = sound_bite.normalize(headroom=0.1)  # dB

            yield self.info_for(type_, transcription, translation, start, sound_bite)

    def info_for(
        self,
        type_: str,
        transcription: str,
        translation: str,
        timestamp: int,
        sound_bite: AudioSegment,
    ):
        """
        Return a tuple of the phrase and its audio.
        """
        assert type_ in ("word", "sentence")
        info = RecordingInfo(
            session=self.session,
            speaker=self.speaker,
            type=type_,
            timestamp=timestamp,
            transcription=transcription,
            translation=translation,
        )
        return info, sound_bite

    def timestamp_within_sentence(self, timestamp: Decimal):
        """
        Return True when the timestamp is found inside a Cree sentence.
        """
        sentences = self.text_grid.tiers[SENTENCE_TIER_CREE]
        sentence = sentences.intervalContaining(timestamp)
        return sentence and sentence.mark != ""


cree_pattern = re.compile(r"\b(?:cree|crk)\b", re.IGNORECASE)
english_pattern = re.compile(r"\b(?:english|eng|en)\b", re.IGNORECASE)


def is_english_tier(tier: IntervalTier) -> bool:
    return bool(english_pattern.search(tier.name))


def is_cree_tier(tier: IntervalTier) -> bool:
    return bool(cree_pattern.search(tier.name))


def to_milliseconds(seconds: Decimal) -> int:
    """
    Converts interval times to an integer in milliseconds.
    """
    return int(seconds * 1000)


def get_mic_id(name: str) -> int:
    """
    Return the microphone number from the filename of the wav file.

    There are at lease five formats in which TextGrid files are named:
    >>> get_mic_id('2_003.TextGrid')
    2
    >>> get_mic_id('2015-05-11am-03.TextGrid')
    3
    >>> get_mic_id('2016-02-24am-Track 2_001.TextGrid')
    2
    >>> get_mic_id('Track 4_001.TextGrid')
    4

    This one is the most annoying format:
    >>> get_mic_id('2015-03-19-Rain-03')
    3
    """
    # Match something like '2016-02-24am-Track 2_001.TextGrid'
    m = re.match(
        r"""
        ^
        (?:                 # An optional "yy-mm-ddtt-Track "
            (?:             # An optional date/time code
                \d{4}       # year
                -
                \d{2}       # month
                -
                \d{2}       # day
                (?:[ap]m)
                -
            )?
            Track\s
        )?

        (\d+)               # THE MIC NUMBER!

        _\d{3}
        (?:[.]TextGrid)?$
        """,
        name,
        re.VERBOSE,
    )
    m = m or re.match(
        r"""
        ^
        \d{4}-\d{2}-\d{2}       # ISO date
        (?:[ap]m)?              # Optional AM/PM
        -
        (?:         # Handle this incredibly specific case:
            Rain-   # It happens three times and I hate it.
        )?

        (\d+)
        (?:[.]TextGrid)?$
        """,
        name,
        re.VERBOSE,
    )
    if not m:
        raise InvalidTextGridName(name)
    return int(m.group(1), 10)
