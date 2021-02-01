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

import logme  # type: ignore
from django.core.management.base import BaseCommand, CommandError  # type: ignore


@logme.log
class Command(BaseCommand):
    """
    Takes all extracted audio files in .wav format
    and writes transcription files for them that can
    then be used by Persephone and Simple4All.
    Files are created in the ./audio directory and stored by speaker
    """

    help = "creates transcription files for persephone and Simple4All"

    def handle(self, *args, **options):

        # Generate this folder by running:
        # python3 manage.py importrecordings --wav --skip-db
        audio_dir = Path("./audio")
        for audio in os.listdir(audio_dir):
            audio_id = audio[:-4]

            conn = sqlite3.connect("./db.sqlite3")
            cur = conn.cursor()

            # Fetch speaker code
            cur.execute(
                f"select speaker_id from validation_recording where id='{audio_id}'"
            )
            speaker = cur.fetchone()
            if speaker:
                speaker = speaker[0]
            else:
                continue

            # Fetch phrase id
            cur.execute(
                f"select phrase_id from validation_recording where id='{audio_id}'"
            )
            phrase_id = cur.fetchone()
            if phrase_id:
                phrase_id = phrase_id[0]

            # Fetch transcription
            cur.execute(
                f"select transcription from validation_phrase where id='{phrase_id}'"
            )
            transcription = cur.fetchone()
            if transcription:
                transcription = transcription[0]

            conn.close()

            # Create necessary directories if they do not exist
            speaker_dir = Path("./audio/" + speaker)
            speaker_audio_dir = Path("./audio/" + speaker + "/audio")
            speaker_persephone_dir = Path("./audio/" + speaker + "/persephone")
            speaker_s4a_dir = Path("./audio/" + speaker + "/s4a")

            for _dir in [
                speaker_dir,
                speaker_audio_dir,
                speaker_persephone_dir,
                speaker_s4a_dir,
            ]:
                if not os.path.isdir(_dir):
                    os.mkdir(_dir)

            # Copy the audio file
            from_dir = Path("./audio/" + audio)
            to_dir = Path("./audio/" + speaker + "/audio/" + audio)
            shutil.copyfile(from_dir, to_dir)

            # Treat the transcription for Persephone and save it
            persephone_file = Path(
                "./audio/" + speaker + "/persephone/" + audio_id + ".txt"
            )
            persephone_trans = transcription.replace(" ", "%")
            persephone_trans = list(persephone_trans)
            persephone_trans = " ".join(persephone_trans)
            persephone_trans = persephone_trans.replace("%", " ")
            with open(persephone_file, "w+") as f:
                f.write(persephone_trans)

            # Save the transcription for Simple4All
            s4a_file = Path("./audio/" + speaker + "/s4a/" + audio_id + ".txt")
            with open(s4a_file, "w+") as f:
                f.write(transcription)

            # Print so we know we're making progress
            print(f"Added phrase {transcription} for speaker {speaker}")
