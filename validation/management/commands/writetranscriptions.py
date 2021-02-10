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
        for audio_file in audio_dir.iterdir():
            audio_id = audio_file.stem
            audio_filename = audio_id + ".wav"

            with closing(sqlite3.connect("./db.sqlite3")) as conn:
                cur = conn.cursor()

                query = """
                select speaker_id, transcription from validation_recording as rec, validation_phrase as p
                where rec.id = ?
                and rec.phrase_id = p.id;
                """

                cur.execute(query, (str(audio_id),))
                result = cur.fetchone()
                speaker = result[0] if result else None
                transcription = result[1] if result else None

            # if there are things that aren't audio files in the directory
            # the speaker variable will be empty, this is normal/fine
            if not speaker:
                continue

            # Create necessary directories if they do not exist
            speaker_dir = audio_dir / speaker
            speaker_audio_dir = audio_dir / speaker / "wav"
            speaker_persephone_dir = audio_dir / speaker / "label"
            speaker_s4a_dir = audio_dir / speaker / "s4a"

            for _dir in [
                speaker_dir,
                speaker_audio_dir,
                speaker_persephone_dir,
                speaker_s4a_dir,
            ]:
                _dir.mkdir(exist_ok=True)

            # Copy the audio file
            from_dir = audio_file
            to_dir = audio_dir / speaker / "wav" / audio_filename
            shutil.copyfile(from_dir, to_dir)

            # Treat the transcription for Persephone and save it
            persephone_filename = audio_id + ".txt"
            persephone_path = audio_dir / speaker / "label" / persephone_filename
            persephone_trans = self.create_persephone_transcription(transcription)
            with open(persephone_path, "w", encoding="UTF=8") as f:
                f.write(persephone_trans)

            # Save the transcription for Simple4All
            s4a_filename = audio_id + ".txt"
            s4a_path = audio_dir / speaker / "s4a" / s4a_filename
            with open(s4a_path, "w", encoding="UTF=8") as f:
                f.write(transcription)

            # Print so we know we're making progress
            print(f"Added phrase {transcription} for speaker {speaker}")

    def create_persephone_transcription(self, transcription):
        """
        Treats the transcription so it can be read by Persephone
        As in, it places a space between all characters, and
        2 spaces between words:
        >>> self.create_persephone_transcription("wâpamêw")
        w â p a m ê w
        >>> self.create_persephone_transcription("kîkwây ôma")
        k î k w â y  ô m a
        """
        assert "%" not in transcription
        persephone_trans = transcription.replace(" ", "%")
        persephone_trans = list(persephone_trans)
        persephone_trans = " ".join(persephone_trans)
        persephone_trans = persephone_trans.replace("%", " ")

        return persephone_trans
