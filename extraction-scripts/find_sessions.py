#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.
# Derived from Praat scripts written by Timothy Mills
#  - extract_items.praat
#  - extract_sessions.praat

import argparse
import logging
import re
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Dict, NamedTuple

from pydub import AudioSegment  # type: ignore
from slugify import slugify  # type: ignore
from textgrid import IntervalTier, TextGrid  # type: ignore

from recval.normalization import normalize
from recval.recording_session import RecordingSession

here = Path('.')
logger = logging.getLogger(__name__)
info = logger.info
warn = logger.warn

parser = argparse.ArgumentParser()
parser.add_argument('master_directory', default=here, type=Path,
                    help='Where to look for session folders')
parser.add_argument('session_codes', default=here / 'speaker-codes.csv', type=Path,
                    help='A TSV that contains codes for sessions...?', nargs='?')


class RecordingInfo(NamedTuple):
    """
    All the information you could possible want to know about a recorded
    snippet.
    """
    session: RecordingSession
    speaker: str
    type: str
    timestamp: str
    transcription: str
    translation: str

    def signature(self) -> str:
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
        return sha256(self.signature().encode('UTF-8')).hexdigest()


class RecordingExtractor:
    """
    Extracts recordings from a directory of sessions.
    """

    def __init__(self) -> None:
        self.sessions: Dict[RecordingSession, Path] = {}

    def scan(self, root_directory: Path):
        """
        Scans the directory provided for sessions.

        For each session directory found, its TextGrid/.wav file pairs are
        scanned for words and sentences.
        """
        info('Scanning %s for sessions...', root_directory)
        for session_dir in root_directory.iterdir():
            if not session_dir.resolve().is_dir():
                info(' ... rejecting %s; not a directory', session_dir)
                continue
            yield from self.extract_session(session_dir)

    def extract_session(self, session_dir: Path):
        session = RecordingSession.from_name(session_dir.stem)
        if session in self.sessions:
            raise RuntimeError(f"Duplicate session: {session} "
                               f"found at {self.sessions[session]}")

        info(' ... Scanning %s for .TextGrid files', session_dir)
        text_grids = list(session_dir.glob('*.TextGrid'))
        info(' ... %d text grids', len(text_grids))

        for text_grid in text_grids:
            sound_file = text_grid.with_suffix('.wav')
            # TODO: tmill's kludge for certain missing filenames???
            if not sound_file.exists():
                warn(' ... ... could not find cooresponding audio for %s',
                     text_grid)
                continue

            assert text_grid.exists() and sound_file.exists()
            info(' ... ... Matching sound file for %s', text_grid)

            # TODO: get speaker from the session-codes table?
            speaker = '???'

            info(' ... ... Extract items from %s using speaker ID %s',
                 sound_file, speaker)
            extractor = PhraseExtractor(session,
                                        AudioSegment.from_file(str(sound_file)),
                                        TextGrid.fromFile(str(text_grid)),
                                        speaker)
            yield from extractor.extract_all()


WORD_TIER_ENGLISH = 0
WORD_TIER_CREE = 1
SENTENCE_TIER_ENGLISH = 2
SENTENCE_TIER_CREE = 3


class PhraseExtractor:
    """
    Extracts recorings from a session directory.
    """
    def __init__(self,
                 session: RecordingSession,
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

        info(' ... ... extracting words')
        yield from self.extract_words(
            cree_tier=self.text_grid.tiers[WORD_TIER_CREE],
            english_tier=self.text_grid.tiers[WORD_TIER_ENGLISH]
        )

        info(' ... ... extracting sentences')
        yield from self.extract_sentences(
            cree_tier=self.text_grid.tiers[SENTENCE_TIER_CREE],
            english_tier=self.text_grid.tiers[SENTENCE_TIER_ENGLISH]
        )

    def extract_words(self, cree_tier, english_tier):
        yield from self.extract_phrases('word', cree_tier, english_tier)

    def extract_sentences(self, cree_tier, english_tier):
        yield from self.extract_phrases('sentence', cree_tier, english_tier)

    def extract_phrases(self, _type: str,
                        cree_tier: IntervalTier, english_tier: IntervalTier):
        assert is_cree_tier(cree_tier), cree_tier.name
        assert is_english_tier(english_tier), english_tier.name

        for interval in cree_tier:
            if not interval.mark or interval.mark.strip() == '':
                # This interval is empty, for some reason.
                continue

            transcription = normalize(interval.mark)

            start = to_milliseconds(interval.minTime)
            end = to_milliseconds(interval.maxTime)
            midtime = (interval.minTime + interval.maxTime) / 2

            # Figure out if this word belongs to a sentence.
            if _type == 'word' and self.timestamp_within_sentence(midtime):
                # It's an example sentence; leave it for the next loop.
                info(' ... ... ... %r is in a sentence', transcription)
                continue

            # Get the word's English gloss.
            english_interval = english_tier.intervalContaining(midtime)
            translation = normalize(english_interval.mark)

            # Snip out the sounds.
            sound_bite = self.sound[start:end]
            # tmills: normalize sound levels (some speakers are very quiet)
            sound_bite.normalize(headroom=0.1)  # dB

            yield self.info_for(_type, transcription, translation,
                                start, sound_bite)

    def info_for(self, _type, transcription, translation, timestamp,
                 sound_bite):
        """
        Return a tuple of the phrase and its audio.
        """
        assert _type in ('word', 'sentence')
        info = RecordingInfo(session=self.session,
                             speaker=self.speaker,
                             type=_type,
                             timestamp=timestamp,
                             transcription=transcription,
                             translation=translation)
        return info, sound_bite

    def timestamp_within_sentence(self, timestamp: Decimal):
        """
        Return True when the timestamp is found inside a Cree sentence.
        """
        sentences = self.text_grid.tiers[SENTENCE_TIER_CREE]
        sentence = sentences.intervalContaining(timestamp)
        return sentence and sentence.mark != ''


cree_pattern = re.compile(r'\b(?:cree|crk)\b', re.IGNORECASE)
english_pattern = re.compile(r'\b(?:english|eng|en)\b', re.IGNORECASE)


def is_english_tier(tier: IntervalTier) -> bool:
    return bool(english_pattern.search(tier.name))


def is_cree_tier(tier: IntervalTier) -> bool:
    return bool(cree_pattern.search(tier.name))


def to_milliseconds(seconds: Decimal) -> int:
    """
    Converts interval times to an integer in milliseconds.
    """
    return int(seconds * 1000)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args()

    # TODO: read session-codes?
    scanner = RecordingExtractor()
    for recording, audio in scanner.scan(root_directory=args.master_directory):
        info(" ... ... ... Exporting:\n%s", recording.signature())
        r = recording
        # Export it.
        slug = slugify(f"{r.type}-{r.transcription}-{r.session}-{r.speaker}-{r.timestamp}",
                       to_lower=True)
        audio.export(str(Path('/tmp') / f"{slug}.wav"))
