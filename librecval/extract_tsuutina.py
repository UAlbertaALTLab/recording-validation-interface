import csv
from hashlib import sha256
from typing import NamedTuple
from typing_extensions import Literal

from pydub import AudioSegment
from pympi.Elan import Eaf

from librecval.recording_session import SessionID

WordOrSentence = Literal["word", "sentence"]
GoodBadUnknown = Literal["good", "bad", "unknown"]


class Segment(NamedTuple):
    translation: str
    transcription: str
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


def run():
    eaf_file = Eaf(
        "/Users/jolenepoulin/Documents/Onespot-Sapir/OS-srs-BRS-018-2015-07-15_0841.eaf"
    )
    keys = eaf_file.get_tier_names()
    print(keys)
    metadata_file = open(
        "/Users/jolenepoulin/Documents/recording-validation-interface/private/tsuutina-metadata.csv"
    )
    metadata = csv.DictReader(metadata_file)
    print(metadata.fieldnames)
    md_dict = {}
    for row in metadata:
        print(row)
        md_dict[row["ID"]] = {
            "form": row["Form"],
            "corrected-form": row["Corrected form"],
            "senses": row["Senses"],
            "fst-gloss-template": row["FST gloss template"],
            "morphemic-parsing": row["Morphemic parsing"],
        }
    # for elem in eaf_file.get_annotation_data_for_tier('BRS-Identifier'):
    #     print(elem[2])
    #     if elem[2] in metadata['ID']:
    #         print(metadata['ID'][elem[2]])

    metadata_file.close()


if __name__ == "__main__":
    run()
