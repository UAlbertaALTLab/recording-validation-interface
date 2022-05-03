import csv
import os
from datetime import datetime
import time
from hashlib import sha256
from os import fspath
from pathlib import Path
from typing import NamedTuple

from django.conf import settings
from typing_extensions import Literal
import re

from pydub import AudioSegment  # type: ignore
from pympi.Elan import Eaf  # type: ignore

from librecval.recording_session import SessionID
from validation.models import Phrase, Recording

WordOrSentence = Literal["word", "sentence"]


class Segment(NamedTuple):
    id: str
    translation: str
    transcription: str
    fixed_transcription: str
    type: WordOrSentence
    start: int
    stop: int
    comment: str
    speaker: str
    quality: str
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
        - Sapir's filesystem and backups don't like diacritics very much
        - we get URL issues trying to load the audio if we use the name
        - other reasons, and good ones, too
        """
        return sha256(self.signature().encode("UTF-8")).hexdigest()


class OkimasisRecordingExtractor:
    """
    Extracts recordings from a directory of Jean Okimâsis's recordings
    """

    def scan(self, sessions_dir):

        sessions_dir = Path(sessions_dir)
        audio_files = list(sessions_dir.glob("*.wav"))
        for audio_file in audio_files:
            print(audio_file)
            session_num = str(audio_file.name).split(" ")[1].replace(".wav", "")
            session_num = f"{int(session_num):02}"
            elan_file_path = Path(
                sessions_dir, f"Okimasis_Track_{session_num}_Annotations.eaf"
            )
            if not elan_file_path.is_file():
                continue

            _eaf = Eaf(elan_file_path)

            for elem in _eaf.get_annotation_data_for_tier("English (sentence)"):
                start = elem[0]
                stop = elem[1]
                translation = elem[2]
                transcription, _type = get_transcription_and_type_from_timestamp(
                    _eaf, start
                )
                rec_date = get_session_from_mtime(os.path.getmtime(audio_file))
                session_id = SessionID(
                    date=datetime.date(rec_date),
                    time_of_day=None,
                    subsession=None,
                    location=None,
                )
                audio = AudioSegment.from_file(fspath(audio_file))[start:stop]
                audio = audio.set_channels(1)
                s = Segment(
                    id="",
                    translation=translation,
                    transcription=transcription,
                    fixed_transcription=transcription,
                    start=start,
                    stop=stop,
                    comment=get_comments_from_eaf(_eaf, start),
                    quality=get_quality_from_eaf(_eaf, start),
                    session=session_id,
                    audio=audio,
                    type=_type,
                    speaker="OKI",
                )

                yield s

    def scan_mp3(self, sessions_dir):
        sessions_dir = Path(sessions_dir)
        audio_files = list(sessions_dir.glob("*.mp3"))
        for audio_file in audio_files:
            word = Path(audio_file).stem

            session = get_session_from_mtime(os.path.getmtime(audio_file))
            session_id = SessionID(
                date=datetime.date(session),
                time_of_day=None,
                subsession=None,
                location=None,
            )

            audio = AudioSegment.from_file(fspath(audio_file))
            audio = audio.set_channels(1)

            s = Segment(
                id="",
                translation="",
                transcription=word,
                fixed_transcription=word,
                start=0,
                stop=0,
                comment="",
                quality=Recording.UNKNOWN,
                session=session_id,
                audio=audio,
                type=Phrase.WORD,
                speaker="OKI",
            )

            yield s


def get_session_from_mtime(mtime):
    mod_time = time.strftime("%Y-%m-%d", time.localtime(mtime))
    return datetime.strptime(mod_time, "%Y-%m-%d")


def get_comments_from_eaf(eaf_file, start):
    comment = eaf_file.get_annotation_data_at_time("Comments", start + 1) or ""
    return comment


def get_quality_from_eaf(eaf_file, start):
    comment = get_comments_from_eaf(eaf_file, start)
    if comment != "":
        comment = comment[0][2]
    if comment:
        if "good" in comment.lower():
            return "good"
    return "unknown"


def get_transcription_and_type_from_timestamp(eaf_file, start):
    transcription = eaf_file.get_annotation_data_at_time("Cree (word)", start + 1)
    if not transcription:
        transcription = eaf_file.get_annotation_data_at_time(
            "Cree (sentence)", start + 1
        )[0][2]
        return transcription, Phrase.SENTENCE
    else:
        transcription = transcription[0][2]
    return transcription, Phrase.WORD
