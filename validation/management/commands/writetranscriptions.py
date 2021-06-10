#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright 2021 Jolene Poulin <jcpoulin@ualberta.ca>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
import sqlite3
import os
import shutil
from contextlib import closing

from django.core.management.base import BaseCommand, CommandError  # type: ignore
from tqdm import tqdm


class Command(BaseCommand):
    """
    Takes all extracted audio files in .wav format
    and writes transcription files for them that can
    then be used by Persephone and Simple4All.
    Files are created in the ./audio directory and stored by speaker
    """

    help = "creates transcription files for Persephone and Simple4All"

    def handle(self, *args, **options):
        # Change this if the raw audio files exist elsewhere!
        _path = "./audio"

        # Generate this folder by running:
        # python3 manage.py importrecordings --wav --skip-db
        audio_dir = Path(_path)

        print("Writing transcriptions for all phrases")
        self.write_transcriptions(audio_dir, mode="all")

        print("Writing transcription for auto-validated phrases")
        self.write_transcriptions(audio_dir, mode="auto-validated")

    def write_transcriptions(self, audio_dir, mode):
        # Change this to Path("/where/you/want/training/data")
        # if you want the data elsewhere
        training_dir = Path("./transcriptions")
        for audio_file in tqdm(
            audio_dir.iterdir(),
            total=sum(1 for x in audio_dir.glob("*") if x.is_file()),
        ):
            audio_id = audio_file.stem

            if mode == "auto-validated":
                query = """
                    select speaker_id, transcription from validation_recording as rec, validation_phrase as p
                    where rec.id = ?
                    and rec.phrase_id = p.id
                    and p.status = "auto-validated";
                    """
            else:
                query = """
                    select speaker_id, field_transcription from validation_recording as rec, validation_phrase as p
                    where rec.id = ?
                    and rec.phrase_id = p.id;
                    """

            with closing(sqlite3.connect("./db.sqlite3")) as conn:
                cur = conn.cursor()

                cur.execute(query, (str(audio_id),))
                result = cur.fetchone()
                speaker = result[0] if result else None
                transcription = result[1] if result else None

            # if there are things that aren't audio files in the directory
            # the speaker variable will be empty, this is normal/fine
            if not speaker or "/" in speaker:
                continue

            self.make_directories(training_dir, speaker)
            self.copy_audio_file(training_dir, audio_file, speaker)

            # Treat the transcription for Persephone and save it
            persephone_filename = audio_id + ".txt"
            if mode == "auto-validated":
                persephone_path = (
                    training_dir / speaker / "auto_val" / "label" / persephone_filename
                )
            else:
                persephone_path = training_dir / speaker / "label" / persephone_filename

            persephone_trans = create_persephone_transcription(transcription)
            with open(persephone_path, "w", encoding="UTF=8") as f:
                f.write(persephone_trans)

            # Save the transcription for Simple4All
            s4a_filename = audio_id + ".txt"
            if mode == "auto-validated":
                s4a_path = training_dir / speaker / "auto_val" / "s4a" / s4a_filename
            else:
                s4a_path = training_dir / speaker / "s4a" / s4a_filename

            s4a_trans = create_s4a_transcription(transcription)
            with open(s4a_path, "w", encoding="UTF=8") as f:
                f.write(s4a_trans)

    def copy_audio_file(self, training_dir, audio_file, speaker):
        # Copy the audio file
        audio_filename = audio_file.stem + ".wav"
        from_dir = audio_file
        to_dir = training_dir / speaker / "wav" / audio_filename
        if not to_dir.is_file():
            shutil.copyfile(from_dir, to_dir)

    def make_directories(self, training_dir, speaker):
        # Create necessary directories if they do not exist
        speaker_dir = training_dir / speaker
        speaker_audio_dir = speaker_dir / "wav"
        speaker_persephone_dir = speaker_dir / "label"
        speaker_s4a_dir = speaker_dir / "s4a"
        speaker_auto_val_dir = speaker_dir / "auto_val"
        speaker_persephone_auto_val_dir = speaker_auto_val_dir / "label"
        speaker_s4a_auto_val_dir = speaker_auto_val_dir / "s4a"

        for _dir in [
            speaker_dir,
            speaker_audio_dir,
            speaker_persephone_dir,
            speaker_s4a_dir,
            speaker_auto_val_dir,
            speaker_persephone_auto_val_dir,
            speaker_s4a_auto_val_dir,
        ]:
            _dir.mkdir(exist_ok=True)


def create_persephone_transcription(transcription):
    """
    Treats the transcription so it can be read by Persephone
    As in, it places a space between all characters, and
    2 spaces between words:
    >>> create_persephone_transcription("wâpamêw")
    'w â p a m ê w'
    >>> create_persephone_transcription("kîkwây ôma")
    'k î k w â y  ô m a'
    """
    assert "%" not in transcription
    persephone_trans = transcription.replace(" ", "%")
    persephone_trans = list(persephone_trans)
    persephone_trans = " ".join(persephone_trans)
    persephone_trans = persephone_trans.replace("%", "")

    return persephone_trans


def create_s4a_transcription(transcription):
    """
    Prepares transcriptions for Simple4All
    >>> create_s4a_transcription("wâpamêw")
    'waapameew'
    >>> create_s4a_transcription("kîkwây ôma")
    'kiikwaay ooma'
    >>> create_s4a_transcription("masinahikan")
    'masinahikan'
    """

    transcription = transcription.replace("ê", "ee")
    transcription = transcription.replace("â", "aa")
    transcription = transcription.replace("î", "ii")
    transcription = transcription.replace("ô", "oo")

    return transcription
