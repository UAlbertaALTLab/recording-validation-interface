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
from librecval.extract import SemanticSegment as Segment


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
