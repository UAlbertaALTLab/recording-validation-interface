#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright 2018 Eddie Antonio Santos <easantos@ualberta.ca>
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

import logme  # type: ignore
from django.core.management.base import BaseCommand, CommandError  # type: ignore

from validation.models import (
    Phrase,
    Recording,
    RecordingSession,
    Speaker,
    LanguageVariant,
)


class Command(BaseCommand):
    help = "given a session and two speaker codes, it changes the speaker in all recordings in the session to the alternative, effectively swapping speakers on tracks."

    def add_arguments(self, parser):
        parser.add_argument("session_id")
        parser.add_argument(
            "--speakers",
            nargs=2,
            help="The short codes used for speakers.  Provide two.",
        )

    def handle(self, *args, session_id, speakers, **options) -> None:
        if len(speakers) == 2:
            session = RecordingSession.objects.get(id=session_id)
            speaker_objects = Speaker.objects.filter(code__in=speakers)
            if speaker_objects.count() == 2:
                self._handle_swap_speakers(
                    session, speaker_objects[0], speaker_objects[1]
                )

    @logme.log
    def _handle_swap_speakers(self, session, speaker_1, speaker_2, logger):
        logger.info(
            f"Swapping speakers {speaker_1.code} and {speaker_2.code} for session {session.id}..."
        )

        speaker_1_recording_ids = [
            entry["id"]
            for entry in session.recording_set.filter(speaker=speaker_1).values("id")
        ]
        speaker_2_recordings = session.recording_set.filter(speaker=speaker_2)

        logger.info(
            f"{speaker_1.code} has {len(speaker_1_recording_ids)} entries and {speaker_2.code} has {speaker_2_recordings.count()} entries."
        )

        logger.info(
            f"Updating all recordings for {speaker_2.code} and resolving issues if there's no wrong word annotation..."
        )
        # Recordings, first side:
        for recording in speaker_2_recordings:
            recording.speaker = speaker_1
            recording.wrong_speaker = False
            recording.save(update_fields=["speaker", "wrong_speaker"])
            issues = recording.issue_set.filter(status="open")
            if issues.count() > 0 and not recording.wrong_word:
                for issue in issues:
                    issue.status = "resolved"
                    issue.save(update_fields=["status"])

        logger.info(
            f"Updating all recordings for {speaker_1.code} and resolving issues if there's no wrong word annotation..."
        )
        for recording in Recording.objects.filter(id__in=speaker_1_recording_ids):
            recording.speaker = speaker_2
            recording.wrong_speaker = False
            recording.save(update_fields=["speaker", "wrong_speaker"])
            issues = recording.issue_set.filter(status="open")
            if issues.count() > 0 and not recording.wrong_word:
                for issue in issues:
                    issue.status = "resolved"
                    issue.save(update_fields=["status"])
        logger.info(f"Ready with session {session.id}.")
