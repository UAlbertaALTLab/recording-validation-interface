import subprocess
from pathlib import Path

import mutagen
from django.conf import settings
from django.core.management.base import BaseCommand

from validation.models import Recording


class Command(BaseCommand):
    help = "removes mouse click from user recordings"

    def handle(self, *args, **kwargs) -> None:
        recordings = Recording.objects.filter(is_user_submitted=True)
        for rec in recordings:
            dest = settings.MEDIA_ROOT + "/" + str(rec.compressed_audio)
            source = dest.replace(".m4a", ".wav")
            if not Path(source).exists():
                continue
            audio_info = mutagen.File(source).info
            if not audio_info.length:
                continue
            new_length = (
                audio_info.length - 0.1
            )  # It takes the average human 0.1 seconds to click down on a button
            subprocess.run(
                ["ffmpeg", "-i", source, "-ss", "0", "-to", str(new_length), dest],
                cwd=settings.MEDIA_ROOT,
            )
            print("Trimmed audio file ", rec.compressed_audio)
