"""
Django management command to import recordings. This assumes the database has
been created.
Its defaults are configured using the following settings:
    MEDIA_ROOT
    RECVAL_AUDIO_PREFIX
    RECVAL_METADATA_PATH
    RECVAL_SESSIONS_DIR
See recvalsite/settings.py for more information.
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError  # type: ignore

from recvalsite import settings
from validation.models import Speaker


class Command(BaseCommand):
    help = "imports speaker images into the database"

    def handle(self, *args, **kwargs) -> None:
        speakers = Speaker.objects.all()
        for speaker in speakers:
            img_name = get_name_from_speaker(speaker)
            path = f"{settings.BIO_IMG_PREFIX}{img_name}"
            if not Path(path).is_file():
                print("Could not find file at", path)
                path = f"{settings.BIO_IMG_PREFIX}missing.jpg"
            speaker.image = path
            speaker.save()


def get_name_from_speaker(speaker):
    name = speaker.full_name
    if not name:
        return "missing.jpg"

    name = name.title()
    name = name.replace("î", "i")
    name = name.replace("â", "a")
    name = name.replace(" ", "")
    return f"{name}.jpg"
