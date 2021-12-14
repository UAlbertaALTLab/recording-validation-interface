import os
import time
from datetime import datetime
from hashlib import sha256
from os import fspath
from pathlib import Path
from typing import NamedTuple

from typing_extensions import Literal

from pydub import AudioSegment  # type: ignore

from librecval.recording_session import SessionID
from validation.models import Recording

GoodBadUnknown = Literal["good", "bad", "unknown"]


class Segment(NamedTuple):
    translation: str
    transcription: str
    fixed_transcription: str
    type: str
    speaker: str
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


class PfnRecordingExtractor:
    """
    Extracts recordings from a directory of Tsuut'ina files
    """

    def scan(self, sessions_dir):
        sessions_dir = Path(sessions_dir)
        audio_files = list(sessions_dir.glob("*.wav"))
        for audio_file in audio_files:
            print(audio_file)

            session = get_session_from_mtime(os.path.getmtime(audio_file))
            session_id = SessionID(
                date=datetime.date(session),
                time_of_day=None,
                subsession=None,
                location=None,
            )

            entry, speaker = get_entry_and_speaker_from_filename(audio_file)
            _type = "sentence" if " " in entry else "word"

            # Must convert stereo sound to mono sound
            # https://stackoverflow.com/questions/5120555/how-can-i-convert-a-wav-from-stereo-to-mono-in-python
            audio = AudioSegment.from_file(fspath(audio_file))
            audio = audio.set_channels(1)

            s = Segment(
                translation=entry,
                transcription="",
                fixed_transcription="",
                quality=Recording.UNKNOWN,
                session=session_id,
                audio=audio,
                type=_type,
                speaker=speaker,
            )

            yield s


def get_entry_and_speaker_from_filename(filename):
    filename = str(filename.name)
    while filename.count("_") > 1:
        filename = filename.replace("_", "'", 1)
    entry, speaker = filename.split("_")
    speaker = speaker.replace(".wav", "")
    return entry, speaker


def get_session_from_mtime(mtime):
    mod_time = time.strftime("%Y-%m-%d", time.localtime(mtime))
    return datetime.strptime(mod_time, "%Y-%m-%d")
