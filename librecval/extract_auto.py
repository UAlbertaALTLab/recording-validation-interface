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
from librecval.extract import Segment


class SynthesizedRecordingExtractor:
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

            entry = get_entry_from_filename(audio_file)

            audio = AudioSegment.from_file(fspath(audio_file))

            s = Segment(
                translation="",
                transcription=entry,
                fixed_transcription="",
                quality=Recording.UNKNOWN,
                session=session_id,
                audio=audio,
                type="word",
                speaker="SDOL",
            )

            yield s


def get_entry_from_filename(filename):
    filename = str(filename.name)
    filename = filename.replace(".wav", "")
    filename = filename.replace("ii", "î")
    filename = filename.replace("ee", "ê")
    filename = filename.replace("aa", "â")
    filename = filename.replace("oo", "ô")
    return filename


def get_session_from_mtime(mtime):
    mod_time = time.strftime("%Y-%m-%d", time.localtime(mtime))
    return datetime.strptime(mod_time, "%Y-%m-%d")
