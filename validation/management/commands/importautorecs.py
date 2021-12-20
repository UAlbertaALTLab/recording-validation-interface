import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import logme
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from pydub import AudioSegment

from librecval.extract_auto import SynthesizedRecordingExtractor
from librecval.extract_pfn import PfnRecordingExtractor
from librecval.extract_tsuutina import TsuutinaRecordingExtractor, Segment
from librecval.extract_tvpd import TvpdRecordingExtractor
from librecval.transcode_recording import transcode_to_aac
from validation.models import (
    Speaker,
    RecordingSession,
    Phrase,
    Recording,
    LanguageVariant,
)


class RecordingError(Exception):
    """
    The error that gets raised if something bad happens with the recording.
    """


class Command(BaseCommand):
    help = "imports auto generated recordings of Dolores Sand into the database"

    def handle(
        self,
        *args,
        store_db=True,
        wav=False,
        audio_dir: Path = Path("./audio"),
        sessions_dir=None,
        **options,
    ) -> None:

        if sessions_dir is None:
            sessions_dir = settings.SYNTH_AUDIO_DIR

        self.audio_dir = audio_dir

        self._handle_store_django(sessions_dir)

    @logme.log
    def _handle_store_django(self, sessions_dir, logger) -> None:
        """
        Stores m4a files, managed by Django's media engine.
        """
        # Store transcoded audio in a temp directory;
        # these files will be then handled by the currently configured storage backend.
        recording_extractor = SynthesizedRecordingExtractor()
        for segment in recording_extractor.scan(sessions_dir):
            rec_id = segment.compute_sha256hash()
            if Recording.objects.filter(id=rec_id).exists():
                continue

            session, session_created = RecordingSession.get_or_create_by_session_id(
                segment.session
            )

            language, language_created = LanguageVariant.objects.get_or_create(
                code="maskwacis"
            )

            speaker, speaker_created = Speaker.objects.get_or_create(
                code=segment.speaker
            )
            speaker.languages.add(language)
            speaker.save()

            kind = Phrase.SENTENCE if segment.type == "sentence" else Phrase.WORD

            phrase, phrase_created = Phrase.objects.get_or_create(
                field_transcription=segment.transcription,
                transcription=segment.fixed_transcription or segment.transcription,
                translation=segment.translation,
                kind=kind,
                origin=Phrase.AUTO,
                language=language,
            )

            recording_path = save_recording(self.audio_dir, segment, segment.audio)
            audio_data = recording_path.read_bytes()
            django_file = ContentFile(audio_data, name=recording_path.name)

            recording = Recording(
                id=rec_id,
                compressed_audio=django_file,
                speaker=speaker,
                timestamp=0,
                phrase=phrase,
                session=session,
                quality=Recording.UNKNOWN,
            )
            recording.clean()
            recording.save()


def save_recording(
    dest: Path,
    info: Segment,
    audio: AudioSegment,
    recording_format="m4a",
) -> Path:
    rec_id = info.compute_sha256hash()
    recording_path = dest / f"{rec_id}.{recording_format}"

    if len(audio) == 0:
        raise RecordingError(f"Recording empty for {info!r}")

    # https://www.ffmpeg.org/doxygen/3.2/group__metadata__api.html
    if recording_format == "m4a":
        transcode_to_aac(
            audio,
            recording_path,
            tags=dict(
                title=info.transcription,
                artist=info.speaker,
                album=info.session,
                language="pfn",
            ),
        )
    else:
        audio.export(os.fspath(recording_path), format="wav")
    assert recording_path.exists()
    return recording_path
