import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from pydub import AudioSegment

from librecval.extract_tsuutina import TsuutinaRecordingExtractor, Segment
from librecval.transcode_recording import transcode_to_aac
from validation.models import Speaker, RecordingSession, Phrase, Recording


class RecordingError(Exception):
    """
    The error that gets raised if something bad happens with the recording.
    """


class Command(BaseCommand):
    help = "imports Tsuut'ina recordings into the database"

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
            sessions_dir = settings.TSUUTINA_SESSIONS_DIR

        self.audio_dir = audio_dir

        self._handle_store_django(sessions_dir)

    def _handle_store_django(self, sessions_dir: Path) -> None:
        """
        Stores m4a files, managed by Django's media engine.
        """
        # Store transcoded audio in a temp directory;
        # these files will be then handled by the currently configured storage backend.
        recording_extractor = TsuutinaRecordingExtractor()
        for segment in recording_extractor.scan():
            print(segment.translation)
            speaker, speaker_created = Speaker.objects.get_or_create(
                code=segment.speaker
            )
            print("SPEAKER ", speaker)

            session, session_created = RecordingSession.get_or_create_by_session_id(
                segment.session
            )
            print(segment.session)

            print("SESSION ", session)

            phrase, phrase_created = Phrase.objects.get_or_create(
                osid=segment.id,
                field_transcription=segment.transcription,
                transcription=segment.fixed_transcription or segment.transcription,
                translation=segment.translation,
                kind=segment.type,
                origin=Phrase.TSUUTINA_DICTIONARY,
            )

            print("PHRASE ", phrase, phrase.id)

            recording_path = save_recording(self.audio_dir, segment, segment.audio)
            audio_data = recording_path.read_bytes()
            django_file = ContentFile(audio_data, name=recording_path.name)

            quality = Recording.GOOD if segment.quality == "good" else Recording.BAD
            rec_id = segment.compute_sha256hash()
            if Recording.objects.filter(id=rec_id).first():
                continue
            recording = Recording(
                id=rec_id,
                compressed_audio=django_file,
                speaker=speaker,
                timestamp=segment.start,
                phrase=phrase,
                session=session,
                quality=quality,
                comment=segment.comment,
            )
            recording.save()

            print("RECORDING ", recording)


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
                language="srs",
            ),
        )
    else:
        audio.export(os.fspath(recording_path), format="wav")
    assert recording_path.exists()
    return recording_path
