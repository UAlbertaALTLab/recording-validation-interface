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
import glob

import logme  # type: ignore
from librecval.normalization import normalize
from librecval.recording_session import SessionID, SessionMetadata
from pydub import AudioSegment  # type: ignore
from pympi.Elan import Eaf  # type: ignore


# ############################### Exceptions ############################### #


class DuplicateSessionError(RuntimeError):
    """
    Raised when the session has already been found by another name.
    """


class MissingMetadataError(RuntimeError):
    """
    Raised when the cooresponding metadata cannot be found.
    """


class InvalidFileName(RuntimeError):
    """
    Raised when the ELAN name does not follow an appropriate pattern.
    """


class MissingTranslationError(RuntimeError):
    """
    Raised when the 'English (word)' and 'English (sentene) tiers
    can not be found in a .eaf file suggesting that the word or phrase
    does not have an existing translation
    """

    # TODO: this is a weird assumption to make. So far it hasn't been an issue though?


# ########################################################################## #


class Segment(NamedTuple):
    """
    Stores an audio segment extracted from a .eaf file
    """

    translation: str  # in English
    transcription: str  # in Cree
    type: str  # "word" or "sentence"
    start: int
    stop: int
    comment: str
    speaker: str
    session: SessionID
    audio: AudioSegment

    def signature(self) -> str:
        # TODO: make this resilient to changing type, transcription, and speaker.
        return (
            f"session: {self.session}\n"
            f"speaker: {self.speaker}\n"
            f"timestamp: {self.start}\n"
            f"{self.type}: {self.transcription}\n"
            "\n"
            f"{self.translation}\n"
        )

    def compute_sha256hash(self) -> str:
        """
        Compute a hash that can be used as a ID for this recording.
        We use the hash instead of including the word in the id for these reasons:
        - we want people to validate the spelling of the word, so
        the word itself might change, making the name meaningless
        - the db doesn't like diacritics very much
        - other reasons, and good ones, too
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

        For each session directory found, its ELAN/.eaf file pairs are
        scanned for words and sentences.
        """
        count = 0

        self.logger.debug("Scanning %s for sessions...", root_directory)
        for session_dir in root_directory.iterdir():
            if not session_dir.resolve().is_dir():
                self.logger.debug("Rejecting %s; not a directory", session_dir)
                continue
            try:
                print(f"Processed folder number {count}")
                count += 1
                yield from self.extract_session(session_dir, count)
            except DuplicateSessionError:
                self.logger.exception("Skipping %s: duplicate", session_dir)
            except MissingMetadataError:
                self.logger.exception("Skipping %s: Missing metadata", session_dir)

    def extract_session(self, session_dir: Path, folder_count):
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

        self.logger.debug("Scanning %s for .eaf files", session_dir)
        annotations = list(session_dir.glob("*.eaf"))
        self.logger.info("%d ELAN files in %s", len(annotations), session_dir)
        count = 0

        for _path in annotations:
            # Find the cooresponding audio with a couple different strategies.
            sound_file = (
                find_audio_from_audacity_format(_path)
                or find_audio_from_audition_format(_path)
                or find_audio_file_with_space(_path)
            )

            if sound_file is None:
                self.logger.warn("Could not find corresponding audio for %s", _path)
                continue

            assert _path.exists() and sound_file.exists()
            self.logger.debug("Matching sound file for %s", _path)

            try:
                mic_id = get_mic_id(_path.stem)
            except InvalidFileName:
                if len(_path) != 1:
                    raise  # There's no way to determine the speaker.
                mic_id = 1
                self.logger.warn("Assuming single text grid is mic 1")

            speaker = self.metadata[session_id][mic_id]

            self.logger.debug(
                "Opening audio and text grid from %s for speaker %s",
                sound_file,
                speaker,
            )

            audio = AudioSegment.from_file(fspath(sound_file))
            print(f"Processed file number {count} from folder number {folder_count}")
            count += 1
            yield from generate_segments_from_eaf(_path, audio, speaker, session_id)


def generate_segments_from_eaf(
    annotation_path: Path, audio: AudioSegment, speaker: str, session_id: SessionID
):

    """
    Yields segements from the annotation file
    """

    # open the EAF
    eaf_file = Eaf(annotation_path)

    keys = eaf_file.get_tier_names()
    count = 0

    # get tiers from keys
    english_word_tier, cree_word_tier = get_word_tiers(keys)
    english_phrase_tier, cree_phrase_tier = get_phrase_tiers(keys)

    comment_tier = "Comments" if "Comments" in keys else None

    if not english_word_tier and english_phrase_tier:
        # Assuming each entry needs to have a translation before continuining
        # Again, this is a weird assumption to make
        raise MissingTranslationError(
            f"No English word or phrase found for data at {annotation_path}"
        )

    # Extract data for Cree words
    cree_words = eaf_file.get_annotation_data_for_tier(cree_word_tier)
    for cree_word in cree_words:
        s, sound_bite = extract_data(
            eaf_file,
            "word",
            cree_word,
            audio,
            speaker,
            session_id,
            english_word_tier,
            comment_tier,
        )
        count += 1
        print(f"Processed audio segment number {count}")
        yield s, sound_bite

    # Extract data for Cree phrases
    cree_phrases = (
        eaf_file.get_annotation_data_for_tier(cree_phrase_tier)
        if cree_phrase_tier
        else []
    )
    for cree_phrase in cree_phrases:
        s, sound_bite = extract_data(
            eaf_file,
            "sentence",
            cree_phrase,
            audio,
            speaker,
            session_id,
            english_phrase_tier,
            comment_tier,
        )
        count += 1
        print(f"Processed audio segment number {count}")
        yield s, sound_bite


def get_word_tiers(keys):

    english_word_tier = "English (word)" if "English (word)" in keys else None
    cree_word_tier = "Cree (word)" if "Cree (word)" in keys else None

    return english_word_tier, cree_word_tier


def get_phrase_tiers(keys):

    english_phrase_tier = "English (sentence)" if "English (sentence)" in keys else None
    cree_phrase_tier = "Cree (sentence)" if "Cree (sentence)" in keys else None

    return english_phrase_tier, cree_phrase_tier


def extract_data(
    _file, _type, snippet, audio, speaker, session_id, english_tier, comment_tier
) -> tuple:
    """
    Extracts all relevant data from a .eaf file, where "relevant data" is:
    - translation
    - transcription
    - start time
    - stop time
    - comment
    Returns a Segment and a sound bite
    """

    start = snippet[0]
    stop = snippet[1]
    transcription = snippet[2]

    translation = _file.get_annotation_data_at_time(english_tier, start + 1)
    translation = (
        translation[0][2] if len(translation) > 0 and len(translation[0]) == 3 else ""
    )

    comment = _file.get_annotation_data_at_time(comment_tier, start + 1) or ""
    comment = comment[0][2] if len(comment) > 0 and len(comment[0]) == 3 else ""

    sound_bite = audio[start:stop]

    # normalize
    transcription = normalize(transcription)
    translation = normalize(translation)
    sound_bite = sound_bite.normalize(headroom=0.1)

    s = Segment(
        translation=translation,  # in English
        transcription=transcription,  # in Cree
        type=_type,
        start=start,
        stop=stop,
        comment=comment,
        speaker=speaker,
        session=session_id,
        audio=sound_bite,
    )

    return s, sound_bite


@logme.log
def find_audio_file_with_space(annotation_path: Path, logger=None) -> Optional[Path]:
    """
    Finds the associated audio in Audacity's format.
    """

    # Get folder name without expected track name
    i = str(annotation_path).rfind("/")
    _path = str(annotation_path)[:i]

    # the track number is between the last - and the last .
    j = str(annotation_path).rfind("-")
    k = str(annotation_path).rfind(".")
    track = str(annotation_path)[j + 1 : k]
    track = track.split("_")[0]

    # find the .wav file
    dirs = list(glob.glob(_path + "/**/" + track + "*.wav", recursive=True))
    sound_file = Path(dirs[0]) if len(dirs) > 0 and Path(dirs[0]).exists() else None
    if not sound_file:
        track = track.replace(" ", "")
        dirs = list(glob.glob(_path + "/**/" + track + ".wav", recursive=True))
        sound_file = Path(dirs[0]) if len(dirs) > 0 and Path(dirs[0]).exists() else None

    logger.debug("[Recorded Subfolder] Trying %s...", sound_file)
    return sound_file


@logme.log
def find_audio_from_audacity_format(
    annotation_path: Path, logger=None
) -> Optional[Path]:
    """
    Finds the associated audio in Audacity's format.
    """
    # TODO: tmill's kludge for certain missing filenames???
    sound_file = annotation_path.with_suffix(".wav")
    logger.debug("[Audacity Format] Trying %s...", sound_file)
    return sound_file if sound_file.exists() else None


@logme.log
def find_audio_from_audition_format(
    annotation_path: Path, logger=None
) -> Optional[Path]:
    #  Gross code to try Adobe Audition recorded files
    session_dir = annotation_path.parent

    # If it's in Audition format, there will be exactly ONE file with the
    # *.sesx extension.
    try:
        (audition_file,) = session_dir.glob("*.sesx")
    except ValueError:
        logger.debug("Could not find exactly one *.sesx file in %s", session_dir)
        return None

    sound_file = (
        session_dir / f"{audition_file.stem}_Recorded" / f"{annotation_path.stem}.wav"
    )
    logger.debug("[Audition Format] Trying %s...", sound_file)
    return sound_file if sound_file.exists() else None


WORD_TIER_ENGLISH = 0
WORD_TIER_CREE = 1
SENTENCE_TIER_ENGLISH = 2
SENTENCE_TIER_CREE = 3


def get_mic_id(name: str) -> int:
    """
    Return the microphone number from the filename of the ELAN file.

    There are at lease five formats in which ELAN files are named:
    >>> get_mic_id('2_003.eaf')
    2
    >>> get_mic_id('2015-05-11am-03.eaf')
    3
    >>> get_mic_id('2016-02-24am-Track 2_001.eaf')
    2
    >>> get_mic_id('Track 4_001.eaf')
    4

    This one is the most annoying format:
    >>> get_mic_id('2015-03-19-Rain-03')
    3
    """
    # Match something like '2016-02-24am-Track 2_001.eaf'
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
        (?:[.]eaf)?$
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
        (?:[.]eaf)?$
        """,
        name,
        re.VERBOSE,
    )
    if not m:
        raise InvalidFileName(name)
    return int(m.group(1), 10)
