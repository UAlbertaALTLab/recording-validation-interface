import os
import time
import csv
from datetime import datetime
from hashlib import sha256
from os import fspath
from pathlib import Path
from typing import NamedTuple

from typing_extensions import Literal

from pydub import AudioSegment  # type: ignore

from librecval.recording_session import SessionID
from recvalsite import settings
from validation.models import Recording

GoodBadUnknown = Literal["good", "bad", "unknown"]


class Segment(NamedTuple):
    translation: str
    transcription: str
    fixed_transcription: str
    type: str
    speaker: str
    semantic: str
    quality: GoodBadUnknown
    session: SessionID
    audio: AudioSegment

    def signature(self) -> str:
        # TODO: make this resilient to changing type, transcription, and speaker.
        return (
            f"session: {self.session}\n"
            f"speaker: {self.speaker}\n"
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


class I3RecordingExtractor:
    """
    Extracts recordings from a directory of Tsuut'ina files
    """

    def scan(self, sessions_dir):
        sessions_dir = Path(sessions_dir)
        metadata_list = []
        with open(settings.I3_METADATA_PATH) as f:
            metadata = csv.reader(f)
            for row in metadata:
                metadata_list.append(row)
        for row in metadata_list:
            audio_file_name = row[0]
            translation = row[1]
            semantic_class = row[2]
            speaker = row[3]
            audio_file = sessions_dir / audio_file_name
            if not audio_file.is_file():
                print(audio_file)
                continue

            session = get_session_from_mtime(os.path.getmtime(audio_file))
            session_id = SessionID(
                date=datetime.date(session),
                time_of_day=None,
                subsession=None,
                location=None,
            )

            _type = "sentence" if " " in translation else "word"

            # Must convert stereo sound to mono sound
            # https://stackoverflow.com/questions/5120555/how-can-i-convert-a-wav-from-stereo-to-mono-in-python
            audio = AudioSegment.from_file(fspath(audio_file))
            audio = audio.set_channels(1)

            s = Segment(
                translation=translation,
                transcription="",
                fixed_transcription="",
                quality=Recording.UNKNOWN,
                session=session_id,
                audio=audio,
                type=_type,
                speaker=speaker,
                semantic=semantic_class,
            )

            yield s


def get_session_from_mtime(mtime):
    mod_time = time.strftime("%Y-%m-%d", time.localtime(mtime))
    return datetime.strptime(mod_time, "%Y-%m-%d")
