from datetime import datetime
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

WordOrSentence = Literal["word", "sentence"]
GoodBadUnknown = Literal["good", "bad", "unknown"]


class Segment(NamedTuple):
    translation: str
    transcription: str
    fixed_transcription: str
    type: WordOrSentence
    start: int
    stop: int
    comment: str
    speaker: str
    quality: GoodBadUnknown
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


class TvpdRecordingExtractor:
    """
    Extracts recordings from a directory of Tsuut'ina files
    """

    def scan(self, sessions_dir):
        sessions_dir = Path(sessions_dir)
        audio_dir = sessions_dir
        elan_files = list(sessions_dir.glob("*.eaf"))
        for elan_file in elan_files:
            print(elan_file)
            elan_file_path = elan_file
            audio_path = Path(audio_dir, elan_file.name.replace(".eaf", ".wav"))
            if not audio_path.is_file():
                continue

            _eaf = Eaf(elan_file_path)
            all_tiers = _eaf.get_tier_names()
            if "BRS-VPD-OriginalText" not in all_tiers:
                continue

            for elem in _eaf.get_annotation_data_for_tier("BRS-VPD-OriginalText"):
                start = elem[0]
                stop = elem[1]
                transcription = elem[2]
                translation = _eaf.get_annotation_data_at_time(
                    "BRS-VPD-OriginalTranslation", start + 1
                )
                if translation:
                    translation = translation[0][2]
                else:
                    translation = ""
                if elan_file.name == "srs-CRIM-20190508-CKCU-01.eaf":
                    temp = translation
                    translation = transcription
                    transcription = temp
                rec_date = get_session_from_filename(elan_file.name)
                session_id = SessionID(
                    date=datetime.date(rec_date),
                    time_of_day=None,
                    subsession=None,
                    location=None,
                )
                if not transcription or not translation:
                    continue
                notes = get_notes(_eaf, all_tiers, start)
                audio = AudioSegment.from_file(fspath(audio_path))[start:stop]
                s = Segment(
                    translation=translation,
                    transcription=transcription,
                    fixed_transcription=transcription,
                    start=start,
                    stop=stop,
                    comment=notes,
                    quality=get_quality_from_notes(notes),
                    session=session_id,
                    audio=audio,
                    type="sentence",
                    speaker="BRS",
                )

                yield s


def get_session_from_filename(filename):
    """
    >>> get_session_from_filename("srs-CRIM-20190507-CKCU-01")
    datetime.datetime(2019, 5, 7, 0, 0)
    """
    date = re.search(r"\d{8}", filename)[0]
    return datetime.strptime(date, "%Y%m%d")


def get_quality_from_notes(notes):
    if not notes:
        return "unknown"
    if "good" in notes.lower():
        return "good"
    elif "bad" in notes.lower():
        return "bad"
    return "unknown"


def get_notes(_eaf, all_tiers, start):
    notes = []
    for tier in all_tiers:
        if tier not in ["BRS-VPD-OriginalText", "BRS-VPD-OriginalTranslation"]:
            info = _eaf.get_annotation_data_at_time(tier, start + 1)
            if info:
                if info[0][2].strip():
                    notes.append(info[0][2])

    return "; ".join(notes)
