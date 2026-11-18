import csv
import unicodedata
from datetime import datetime
from hashlib import sha256
from os import fspath
from pathlib import Path
import re
from typing import NamedTuple

from django.conf import settings
from pydub import AudioSegment  # type: ignore
from typing_extensions import Literal

from librecval.recording_session import SessionID

WordOrSentence = Literal["word", "sentence"]
GoodBadUnknown = Literal["good", "bad", "unknown"]


class Segment(NamedTuple):
    transcription: str
    speaker: str
    audio: AudioSegment

    def signature(self) -> str:
        return (
            f"transcription: {self.transcription}\n"
            f"speaker: {self.speaker}\n"
            f"data: {self.audio.raw_data.hex()}\n"
            "\n"
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


class NehiyawetanDemoRecordingExtractor:
    """
    Extracts recordings from a directory of Nehiyawetan examples
    """

    def scan(self, audio_dir: Path, metadata_file: Path):
        with open(metadata_file, "r") as f:
            entries: list[str] = f.read().splitlines()
            for entry in entries:
                audio_path = Path(audio_dir, entry + ".wav")
                if not audio_path.is_file():
                    # This conversion was needed for locale issues in Linux (at the server)
                    audio_path = Path(
                        audio_dir, unicodedata.normalize("NFD", entry + ".wav")
                    )
                    if not audio_path.is_file():
                        continue
                audio = AudioSegment.from_file(fspath(audio_path))
                s = Segment(transcription=entry, speaker="ROS", audio=audio)

                yield s
