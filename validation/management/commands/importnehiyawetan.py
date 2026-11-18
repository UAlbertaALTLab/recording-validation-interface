from datetime import datetime
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
import logme
from pydub import AudioSegment

from librecval.extract_nehiyawetan import Segment, NehiyawetanDemoRecordingExtractor
from librecval.transcode_recording import transcode_to_aac
from validation.models import (
    Collection,
    LanguageVariant,
    Phrase,
    Recording,
    RecordingSession,
    Speaker,
)


class RecordingError(Exception):
    """
    The error that gets raised if something bad happens with the recording.
    """


class Command(BaseCommand):
    help = "imports Tsuut'ina recordings into the database"

    def add_arguments(self, parser):
        parser.add_argument("sessions_dir", nargs="?", type=Path, default="./")
        parser.add_argument(
            "--audio-dir",
            type=Path,
            help="where to store the extracted audio",
            default=Path("./audio"),
        )
        parser.add_argument(
            "--metadata-file",
            type=Path,
            help="where the list of files is stored",
            default=Path("./nehiyawetan_demo_sentences.txt"),
        )
        parser.add_argument(
            "--collection", type=str, help="Collection Name", default="OAHPA0"
        )

    def handle(
        self,
        *args,
        store_db=True,
        wav=False,
        audio_dir: Path,
        sessions_dir: Path,
        metadata_file: Path,
        collection: str,
        **options,
    ) -> None:

        self.audio_dir = audio_dir

        self._handle_store_django(sessions_dir, metadata_file, collection)

    @logme.log
    def _handle_store_django(
        self, sessions_dir: Path, metadata_file: Path, collection_name: str, logger
    ) -> None:
        """
        Stores m4a files, managed by Django's media engine.
        """
        # Store transcoded audio in a temp directory;
        # these files will be then handled by the currently configured storage backend.
        recording_extractor = NehiyawetanDemoRecordingExtractor()
        collection, _ = Collection.objects.get_or_create(code=collection_name)
        for segment in recording_extractor.scan(
            sessions_dir, metadata_file
        ):  # type: Segment
            logger.info(f"Processing {segment.transcription}...")
            rec_id = segment.compute_sha256hash()
            if Recording.objects.filter(id=rec_id).exists():
                continue

            speaker, speaker_created = Speaker.objects.get_or_create(
                code=segment.speaker
            )

            language, language_created = LanguageVariant.objects.get_or_create(
                code="nehiyawetan", name="Nehiyawetan-Oahpa"
            )

            phrase, phrase_created = Phrase.objects.get_or_create(
                field_transcription=segment.transcription,
                transcription=segment.transcription,
                kind=Phrase.SENTENCE if " " in segment.transcription else Phrase.WORD,
                origin=Phrase.NEW_WORD,
                language=language,
            )

            recording_path = save_recording(
                self.audio_dir, segment, segment.audio, collection_name
            )
            audio_data = recording_path.read_bytes()
            django_file = ContentFile(audio_data, name=recording_path.name)

            quality = Recording.GOOD
            recording = Recording(
                id=rec_id,
                compressed_audio=django_file,
                speaker=speaker,
                timestamp=0,
                phrase=phrase,
                quality=quality,
                comment="",
                collection=collection,
            )
            recording.clean()
            recording.save()


def save_recording(
    dest: Path,
    info: Segment,
    audio: AudioSegment,
    collection_name: str,
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
                album=collection_name,
                language="crk",
            ),
        )
    else:
        audio.export(os.fspath(recording_path), format="wav")
    assert recording_path.exists()
    return recording_path
