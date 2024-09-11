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
from typing import Dict, Iterable, NamedTuple, Optional, Tuple

import logme  # type: ignore
from pydub import AudioSegment  # type: ignore
from pympi.Elan import Eaf  # type: ignore
from typing_extensions import Literal

from librecval.normalization import normalize
from librecval.recording_session import SessionID, SessionMetadata, SessionParseError

# Path to project root directory.
project_root = Path(__file__).parent.parent
assert (project_root / "LICENSE").exists()


# ############################### Exceptions ############################### #


class MissingMetadataError(RuntimeError):
    """
    Raised when the corresponding metadata cannot be found.
    """


class InvalidFileName(RuntimeError):
    """
    Raised when the ELAN name does not follow an appropriate pattern.
    """


class InvalidAnnotationError(RuntimeError):
    """
    Raised when the ELAN file is unusable and should be ignored!
    """


class InvalidSpeakerCode(RuntimeError):
    """
    Raised when the speaker code is null
    """


class MissingTranslationError(RuntimeError):
    """
    Raised when the 'English (word)' and 'English (sentence)' tiers
    can not be found in a .eaf file suggesting that the word or phrase
    does not have an existing translation
    """

    # TODO: this is a weird assumption to make. So far it hasn't been an issue though?


# ########################################################################## #

WordOrSentence = Literal["word", "sentence"]


class Segment(NamedTuple):
    """
    Stores an audio segment extracted from a .eaf file
    """

    english_translation: str
    cree_transcription: str
    type: WordOrSentence
    start: int
    stop: int
    comment: str
    speaker: str
    quality: str  # one of: good, bad, unknown
    session: SessionID
    audio: AudioSegment

    def signature(self) -> str:
        # TODO: make this resilient to changing type, transcription, and speaker.
        return (
            f"session: {self.session}\n"
            f"speaker: {self.speaker}\n"
            f"timestamp: {self.start}\n"
            f"{self.type}: {self.cree_transcription}\n"
            "\n"
            f"{self.english_translation}\n"
        )

    def compute_sha256hash(self) -> str:
        """
        Compute a hash that can be used as a ID for this recording.
        We use the hash instead of including the word in the id for these reasons:
        - we want people to validate the spelling of the word, so
        the word itself might change, making the name meaningless
        - Sapir's filesystem and backups don't like diacritics very much
        - we get URL issues trying to load the audio if we use the name
        - other reasons, and good ones, too
        """
        return sha256(self.signature().encode("UTF-8")).hexdigest()


# One recording, with all its metadata along with its audio.
SegmentAndAudio = Tuple[Segment, AudioSegment]


@logme.log
class RecordingExtractor:
    """
    Extracts recordings from a directory of sessions.
    """

    logger: logging.Logger

    def __init__(self, metadata=Dict[SessionID, SessionMetadata]) -> None:
        self.metadata = metadata

    def scan(self, root_directory: Path) -> Iterable[SegmentAndAudio]:
        """
        Scans the directory provided for sessions.

        For each session directory found, its ELAN/.eaf file pairs are
        scanned for words and sentences.
        """

        self.logger.debug("Scanning %s for sessions...", root_directory)

        valid_session_directories = []

        for session_dir in root_directory.iterdir():
            if not session_dir.resolve().is_dir():
                self.logger.debug("Rejecting %s; not a directory", session_dir)
                continue
            valid_session_directories.append(session_dir)

        for session_dir in valid_session_directories:
            try:
                yield from self.extract_all_recordings_from_session(session_dir)
            except Exception:
                session_id = get_session_name_or_none(session_dir)
                if session_id is None:
                    continue

                self.logger.exception("Error extracting %s", session_dir)
                failed_dir = project_root / "failed-sessions"
                failed_dir.mkdir(exist_ok=True)
                name = failed_dir / session_id.as_filename()
                if not name.exists():
                    self.logger.error("failed ONCE again: %s", session_dir)
                    name.symlink_to(session_dir)
                continue

    def extract_all_recordings_from_session(
        self, session_dir: Path
    ) -> Iterable[SegmentAndAudio]:
        try:
            yield from self.extract_session(session_dir)
        except MissingMetadataError:
            self.logger.exception("Skipping %s: Missing metadata", session_dir)

    def extract_session(self, session_dir: Path) -> Iterable[SegmentAndAudio]:
        """
        Extracts recordings from a single session.
        """
        try:
            session_id = SessionID.from_name(session_dir.stem)
        except SessionParseError:
            session_id = SessionID.parse_dirty(session_dir.stem)
        if session_id not in self.metadata:
            raise MissingMetadataError(f"Missing metadata for {session_id}")

        self.logger.debug("Scanning %s for .eaf files", session_dir)
        annotations = list(session_dir.glob("*.eaf"))
        self.logger.info("%d ELAN files in %s", len(annotations), session_dir)

        for _path in annotations:
            # Find the corresponding audio with a couple different strategies.
            sound_file = (
                find_audio_from_audacity_format(_path)
                or find_audio_from_audition_format(_path)
                or find_audio_oddities(_path)
            )

            if sound_file is None:
                self.logger.warning("Could not find corresponding audio for %s", _path)
                continue

            assert _path.exists() and sound_file.exists()
            self.logger.debug("Matching sound file for %s", _path)

            try:
                mic_id = get_mic_id(_path.stem)
                recording_mic_id = get_mic_id(sound_file.stem)
                if mic_id != recording_mic_id:
                    self.logger.error(
                        "Attempted to match a track with a different mic id to an ELAN file: %s and %s",
                        _path.stem,
                        sound_file.stem,
                    )
                    continue
            except InvalidFileName:
                if len(annotations) != 1:
                    raise  # There's no way to determine the speaker.
                mic_id = 1
                self.logger.warning("Assuming single ELAN file is mic 1")

            speaker = self.metadata[session_id][mic_id]

            if speaker is None:
                raise InvalidSpeakerCode

            self.logger.debug(
                "Opening audio and .eaf from %s for speaker %s",
                sound_file,
                speaker,
            )

            audio = AudioSegment.from_file(fspath(sound_file))
            yield from generate_segments_from_eaf(_path, audio, speaker, session_id)


def generate_segments_from_eaf(
    annotation_path: Path, audio: AudioSegment, speaker: str, session_id: SessionID
) -> Iterable[SegmentAndAudio]:
    """
    Yields segements from the annotation file
    """

    # open the EAF
    eaf_file = Eaf(annotation_path)

    keys = eaf_file.get_tier_names()

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
    _file,
    _type: WordOrSentence,
    snippet,
    audio,
    speaker,
    session_id,
    english_tier,
    comment_tier,
) -> SegmentAndAudio:
    """
    Extracts all relevant data from a .eaf file, where "relevant data" is:
    - translation
    - transcription
    - start time
    - stop time
    - comment
    - quality
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

    quality = "unknown"
    if "good" in comment.lower() or "best" in comment.lower():
        quality = "good"
    elif "bad" in comment.lower():
        quality = "bad"

    sound_bite = audio[start:stop]

    # normalize
    transcription = normalize(transcription)
    translation = normalize(translation)
    sound_bite = sound_bite.normalize(headroom=0.1)

    s = Segment(
        english_translation=translation,
        cree_transcription=transcription,
        type=_type,
        start=start,
        stop=stop,
        comment=comment,
        speaker=speaker,
        quality=quality,
        session=session_id,
        audio=sound_bite,
    )

    return s, sound_bite


@logme.log
def find_audio_oddities(annotation_path: Path, logger=None) -> Optional[Path]:
    """
    Finds the associated audio in Audacity's format.
    NOTE: This method does not check for a single file option, but is trying its best to match to something.
    Thus, if there are multiple options, it will take the first.  This has been a problem in the past.
    """

    # Get folder name without expected track name
    _path = annotation_path.parent
    sound_file = None

    # the track number is between the last - and the last .
    match = re.match(
        r"""
        .*-(
            [^-]+
            )
            \.
            [^-.]+
        """,
        str(annotation_path),
        re.VERBOSE,
    )
    if match:
        track = match.group(1)
        track_1 = track.split("_")[0]

        # try 1: the .wav file is in a subfolder, but it has 'Track number' in it
        dirs = list(_path.glob(f"**/{track}*.wav"))
        sound_file = Path(dirs[0]) if len(dirs) > 0 and Path(dirs[0]).exists() else None

    if not sound_file:
        # try 1b: the .wav file is in a subfolder, but it has 'Track number' in it,
        #         ** without leading zeros **
        track_1 = track.split("_")[0]
        try:
            track_2 = str(int(track.split("_")[1]))
            dirs = [
                path
                for path in _path.glob(f"**/{track_1} {track_2}*.wav")
                if Path(path).exists()
            ]
            sound_file = Path(dirs[0]) if len(dirs) == 1 else None
        except ValueError:
            pass

    if not sound_file:
        # try 1c: the .wav file is in a subfolder, but it has 'Track number' in it,
        #         ** without leading zeros **
        track_1 = track.split("_")[0]
        try:
            track_2 = "_".join(track.split("_")[1:])
            dirs = [
                path
                for path in _path.glob(f"**/{track_1} {track_2}*.wav")
                if Path(path).exists()
            ]
            sound_file = Path(dirs[0]) if len(dirs) == 1 else None
        except ValueError:
            pass

    if not sound_file:
        # try 2: the .wav file has no space between 'Track' and the number
        track_2 = track_1.replace(" ", "")
        dirs = list(_path.glob(f"**/{track_2}*.wav"))
        sound_file = (
            Path(dirs[0]) if len(dirs) == 1 and Path(dirs[0]).exists() else None
        )

    if not sound_file:
        # try 3: the .wav file does have a space between 'Track' and the number
        # This try covers audio file names that DO NOT have the date in them
        track_split = track.split("_")
        n = 0
        j = 0
        for n in range(len(track_split)):
            if "TRACK" in track_split[n].upper():
                j = n
            n += 1

        track_3 = ""
        while j < len(track_split):
            track_3 = track_3 + str(track_split[j]) + "_"
            j += 1

        track_3 = track_3[:-1]
        dirs = list(_path.glob(f"**/{track_3}*.wav"))
        sound_file = (
            Path(dirs[0]) if len(dirs) == 1 and Path(dirs[0]).exists() else None
        )
        if not sound_file:
            track_4 = track_3.replace("Track", "Track ")
            dirs = list(_path.glob(f"**/{track_4}*.wav"))
            sound_file = (
                Path(dirs[0]) if len(dirs) == 1 and Path(dirs[0]).exists() else None
            )
        if not sound_file:
            track_5 = track_3.replace(" ", "")
            track_5 = track_5.replace("Track_", "Track ")
            dirs = list(_path.glob(f"**/{track_5}*.wav"))
            sound_file = (
                Path(dirs[0]) if len(dirs) == 1 and Path(dirs[0]).exists() else None
            )
        if not sound_file:
            track_6 = track_3.replace("track", "Track")
            dirs = list(_path.glob(f"**/{track_6}*.wav"))
            sound_file = (
                Path(dirs[0]) if len(dirs) == 1 and Path(dirs[0]).exists() else None
            )
        if not sound_file:
            track_7 = track_3.replace("Track 0", "Track ")
            dirs = list(_path.glob(f"**/{track_7}*.wav"))
            sound_file = (
                Path(dirs[0]) if len(dirs) == 1 and Path(dirs[0]).exists() else None
            )

    if not sound_file:
        # try 8: the .wav file has the same name as the .eaf file
        # EXCEPT the .eaf file has the word 'Track_' in it
        # This option DOES NOT have the word 'Track' in it
        # and it DOES have the date in it
        track_8 = str(annotation_path.stem)
        track_8 = track_8.replace("Track_", "")
        dirs = list(_path.glob(f"**/{track_8}*.wav"))
        sound_file = Path(dirs[0]) if len(dirs) > 0 and Path(dirs[0]).exists() else None
        if not sound_file:
            track_9 = track_8.replace("am", "")
            track_9 = track_9.replace("pm", "")
            track_9 = track_9.replace("AM", "")
            track_9 = track_9.replace("PM", "")
            dirs = list(_path.glob(f"**/{track_9}*.wav"))
            sound_file = (
                Path(dirs[0]) if len(dirs) > 0 and Path(dirs[0]).exists() else None
            )

    if not sound_file:
        # try 13: the .wav file is not in a subfolder, but also doesn't have the word "Track" in it
        # BUT ALSO the .eaf file has am/pm in it and the .wav file does not
        track_13 = str(annotation_path.stem)
        track_13 = track_13.replace("am", "")
        track_13 = track_13.replace("AM", "")
        track_13 = track_13.replace("pm", "")
        track_13 = track_13.replace("PM", "")

        dirs = list(_path.glob(f"{track_13}*.wav"))
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

    Here are the currently known "conventions" for naming the ELAN files.
    >>> get_mic_id('2_003.eaf')
    2
    >>> get_mic_id('Track 4_001.eaf')
    4
    >>> get_mic_id('2015-03-19-Rain-03')
    3
    >>> get_mic_id('2015-05-11am-03.eaf')
    3
    >>> get_mic_id('2016-04-18am_track 4_')
    4
    >>> get_mic_id('2017-05-18pm-US-Track_03')
    3
    >>> get_mic_id('2018-04-25am-OFF-Track_01')
    1
    >>> get_mic_id('2016-06-13am1-Track 3_001')
    3
    >>> get_mic_id('2016-06-10pm-2-Track 2_001')
    2
    >>> get_mic_id('2017-06-01pmUS-Track 1_001')
    1
    >>> get_mic_id('2017-03-09U Spm-Track 1_001')
    1
    >>> get_mic_id('2016-10-17pm-ds-Track 2_001')
    2
    >>> get_mic_id('2015-04-29-PM-___-_Track_02')
    2
    >>> get_mic_id('2016-02-24am-Track 2_001.eaf')
    2
    >>> get_mic_id('2016-11-21-AM-US-_Record_Track1_001')
    1
    >>> get_mic_id('2017-04-20am-US_Recorded_Track3_001')
    3
    >>> get_mic_id('2016-11-28am_-US-Recorded_Track2_001')
    2
    >>> get_mic_id('2016-11-21-AM-US-_Recorded_Track2_001')
    2
    >>> get_mic_id('2017-02-16pm-DS_Recorded_Track2_001_1')
    2

    Unknown formats will raise InvalidFileName error.
    """

    IDIOSYNCRACTIC_FORMATS = {
        "Track 3 _001 2016-10-03am-ds": 3,
        "2017-03-USpm-Track 3_001": 3,
        "2016-05-02pm_ Track 1_003": 1,
        "2016-04-20am_ Track 2": 2,
    }

    KNOWN_BAD_ANNOTATION_FILES = {
        # Looks like annotator tried annotating ALL THREE TRACKS in this file at once,
        # but then gave up and made separate files for each track (as became standard).
        # See: /data/av/backup-mwe/2015-05-12pm
        "2105-05-12pm",
        # There are newer, better annotations in this directory that superceed this
        # annotation which is for mic 2, but should be disregarded in preference for the
        # newer annotations.
        # See: /data/av/backup-mwe/2015-03-19
        "2015-03-10-Rain_data",
    }

    # Match something like '2016-02-24am-Track 2_001.eaf'
    m = re.match(
        r"""
        ^
        (?:                 # An optional "yy-mm-ddtt-US-Track "
            (?:             # An optional date/time code
                \d{4}       # year
                -
                \d{2}       # month
                -
                \d{2}       # day
                (?:         # the first possible place for the location 😨
                    [UD][ ]?S
                )?
                (?i:        # case-insensitive AM/PM
                    -?
                    [AP]M
                    \d?     # subsession
                )?
                (?i:        # case-insensitive Location
                   [_-]*
                   (?: US|DS|KCH|OFF|[1234]|___)
                )?
                (?:
                    [_-]+
                    Record(?:ed)?
                )?
                [_-]        # one MANDATORY separator
                [_-]?       # account for extra separator ¯\_(ツ)_/¯
            )?
            [tT]rack[_ -]?
        )?
        0*                  # ignore leading zeros
        (\d)                # THE MIC NUMBER!
        (?:                 # there might be stuff after, but we've already parsed the mic ID so.... ✌️
            _
            .*
        )?
        (?:[.]eaf)?
        $
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
        if name in KNOWN_BAD_ANNOTATION_FILES:
            raise InvalidAnnotationError(
                f"Tried to get mic for known bad annotation file: {name}"
            )
        if name in IDIOSYNCRACTIC_FORMATS:
            return IDIOSYNCRACTIC_FORMATS[name]
        raise InvalidFileName(f"Could not determine mic number from: {name}")
    return int(m.group(1), 10)


@logme.log
def get_session_name_or_none(session_dir: Path, logger=None) -> Optional[SessionID]:
    """
    Returns the session ID from the given path and tries not to crash.
    Returns None if it crashed :/
    """
    try:
        session_id = SessionID.from_name(session_dir.stem)
    except SessionParseError:
        logger.exception("Invalid session name %s", session_dir)
        return None
    return session_id
