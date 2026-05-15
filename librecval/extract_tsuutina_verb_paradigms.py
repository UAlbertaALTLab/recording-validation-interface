import csv
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
            f"language: srs\n"
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


class TsuutinaRecordingExtractor:
    """
    Extracts recordings from a directory of Tsuut'ina files
    """

    def scan(self, sessions_dir, metadata_file):
        md_dict = get_metadata_from_file(metadata_file)

        sessions_dir = Path(sessions_dir)
        audio_dir = Path(sessions_dir)  # settings.TSUUTINA_AUDIO_PREFIX)
        elan_files = list(sessions_dir.glob("*.eaf"))

        for elan_file in elan_files:
            print(elan_file)
            audio_path = Path(audio_dir, md_dict[elan_file.name]["audio"])
            if not audio_path.is_file():
                continue

            # Do this once instead of generating it every time.
            audio_segment = AudioSegment.from_file(fspath(audio_path))

            _eaf = Eaf(elan_file)
            if "BRS" not in _eaf.get_tier_names():
                continue

            annotations = [
                ann
                for ann in _eaf.get_annotation_data_for_tier("BRS")
                if _eaf.get_annotation_data_at_time("BRS-OriginalTranslation", ann[0])
                and _eaf.get_annotation_data_at_time("BRS-OriginalText", ann[0])
            ]

            for elem in annotations:
                transcription = elem[2]
                start = elem[0]
                stop = elem[1]
                rec_date, subsession = get_session_from_filename(elan_file.name)
                translation = ";".join(
                    [
                        ann[2]
                        for ann in _eaf.get_annotation_data_at_time(
                            "BRS-OriginalTranslation", start
                        )
                    ]
                )
                session_id = SessionID(
                    date=datetime.date(rec_date),
                    time_of_day=None,
                    subsession=subsession,
                    location=None,
                )
                audio = audio_segment[start:stop]
                comment = "\n".join(
                    [
                        ";".join(
                            [
                                ann[2]
                                for ann in _eaf.get_annotation_data_at_time(
                                    "BRS-OriginalText", start
                                )
                            ]
                        ),
                        ";".join(
                            [
                                ann[2]
                                for ann in _eaf.get_annotation_data_at_time(
                                    "BRS-Questions", start
                                )
                            ]
                        ),
                    ]
                )
                s = Segment(
                    transcription=transcription,
                    fixed_transcription=transcription,
                    translation=translation,
                    quality=(
                        "unknown"
                        if _eaf.get_annotation_data_at_time("BRS-Questions", start)
                        else "good"
                    ),
                    start=start,
                    stop=stop,
                    session=session_id,
                    audio=audio,
                    type="sentence",
                    speaker="BRS",
                    comment=comment,
                )
                yield s
        return


def get_metadata_from_file(metadata_file):
    metadata_file = open(metadata_file)  # (settings.TSUUTINA_METADATA_PATH)
    metadata = csv.DictReader(
        metadata_file,
        delimiter="\t",
        fieldnames=(["Audio", "ELAN", "Duration", "Contents"]),
    )
    md_dict = {}
    for row in metadata:
        md_dict[row["ELAN"]] = {
            "audio": row["Audio"],
            "elan": row["ELAN"],
            "duration": row["Duration"],
            "contents": row["Contents"],
        }

    metadata_file.close()
    return md_dict


def get_session_from_filename(filename):
    date = re.search(
        r"srs-TLL-(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})-(?P<session>\d{2})",
        filename,
    )
    if not date:
        date = re.search(
            r"srs-TLL-(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})-.*(?P<session>\d{2})?\.eaf",
            filename,
        )
    _datetime = date.groupdict()
    return (
        datetime(
            year=int(_datetime["year"]),
            month=int(_datetime["month"]),
            day=int(_datetime["day"]),
        ),
        int(_datetime.get("session","01")),
    )


def get_quality_from_eaf(eaf_file, start):
    comment = eaf_file.get_annotation_data_at_time("BRS-Questions", start + 1) or ""
    if comment != "":
        comment = comment[0][2]
    if comment:
        if "good" in comment.lower():
            return "good"
        else:
            return "bad"
    return "bad"
