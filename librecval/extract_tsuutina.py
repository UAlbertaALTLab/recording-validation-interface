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
    id: str
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


"""
For each .eaf file in the folder, iterate through the ID tier
store the start and stop times, as well as the ID
Use the metadata sheet to find the transcription(s) and translation
The speaker is always Bruce Starlight -- BRS
The session has to come from the filename
"""


class TsuutinaRecordingExtractor:
    """
    Extracts recordings from a directory of Tsuut'ina files
    """

    def scan(self, sessions_dir):
        md_dict = get_metadata_from_file()

        sessions_dir = Path(sessions_dir)
        audio_dir = Path(settings.TSUUTINA_AUDIO_PREFIX)
        elan_files = list(sessions_dir.glob("*.eaf"))
        for elan_file in elan_files:
            print(elan_file)
            elan_file_path = elan_file
            audio_path = Path(audio_dir, elan_file.name.replace(".eaf", "-ELAN.wav"))
            if not audio_path.is_file():
                continue

            _eaf = Eaf(elan_file_path)
            if "BRS-Identifier" not in _eaf.get_tier_names():
                continue

            for elem in _eaf.get_annotation_data_for_tier("BRS-Identifier"):
                if elem[2] in md_dict.keys():
                    entry = md_dict[elem[2]]
                    if entry["form"].startswith("*"):
                        continue
                    start = elem[0]
                    stop = elem[1]
                    rec_date = get_session_from_filename(elan_file.name)
                    session_id = SessionID(
                        date=datetime.date(rec_date),
                        time_of_day=None,
                        subsession=None,
                        location=None,
                    )
                    audio = AudioSegment.from_file(fspath(audio_path))[start:stop]
                    s = Segment(
                        id=elem[2],
                        translation=entry["senses"],
                        transcription=entry["form"],
                        fixed_transcription=entry["corrected-form"],
                        start=start,
                        stop=stop,
                        comment=entry["notes"],
                        quality=get_quality_from_eaf(_eaf, start),
                        session=session_id,
                        audio=audio,
                        type="word",
                        speaker="BRS",
                    )

                    yield s


def get_metadata_from_file():
    metadata_file = open(settings.TSUUTINA_METADATA_PATH)
    metadata = csv.DictReader(metadata_file)
    md_dict = {}
    for row in metadata:
        md_dict[row["ID"]] = {
            "form": row["Form"],
            "corrected-form": row["Corrected form"],
            "senses": row["Senses"],
            "fst-gloss-template": row["FST gloss template"],
            "morphemic-parsing": row["Morphemic parsing"],
            "aspect": row["Aspect"],
            "argument-structure": row["Argument structure"],
            "inflectional-paradigm": row["Inflectional paradigm"],
            "fst-lemma": row["FST lemma"],
            "fst-morphology": row["FST morphology"],
            "source": row["Source"],
            "fst-status": row["FST status"],
            "notes": row["Notes"],
            "wordnet": row["WordNet"],
            "rapidword-items": row["RapidWords items"],
            "rapidwords-labels": row["RapidWords labels"],
        }

    metadata_file.close()
    return md_dict


def get_session_from_filename(filename):
    date = re.search(r"\d{4}-\d{2}-\d{2}", filename)
    _datetime = date.group().split("-")
    return datetime(
        year=int(_datetime[0]), month=int(_datetime[1]), day=int(_datetime[2])
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
