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
    help = "change all recordings of one speaker to another, useful for retagging and merging.  If you need to swap speakers, use swapspeakersinsession."

    def add_arguments(self, parser):
        parser.add_argument("session_id")
        parser.add_argument(
            "--speaker-from",
            nargs="?",
            help="The short code of the speaker whose recordings would be changed.",
            required=True,
        )
        parser.add_argument(
            "--speaker-to",
            nargs="?",
            help="The short code of the speaker that will be assigned to all recordings of speaker-from.",
            required=True,
        )

    def handle(self, *args, session_id, speaker_from, speaker_to, **options) -> None:
        session = RecordingSession.objects.get(id=session_id)
        speaker_from = Speaker.objects.get(code=speaker_from)
        speaker_to = Speaker.objects.get(code=speaker_to)
        self._handle_change_speaker(session, speaker_from, speaker_to)

    @logme.log
    def _handle_change_speaker(self, session, speaker_from, speaker_to, logger):

        logger.info(
            f"Reannotating all recordings from session {session.id} that had speaker {speaker_from.code} to have instead speaker {speaker_to.code}..."
        )
        recordings = session.recording_set.filter(speaker=speaker_from)

        logger.info(
            f"Changing {recordings.count()} recordings and resolving issues if there's no wrong word annotation..."
        )

        # Recordings, first side:
        for recording in recordings:
            recording.speaker = speaker_to
            recording.wrong_speaker = False
            recording.save(update_fields=["speaker", "wrong_speaker"])
            issues = recording.issue_set.filter(status="open")
            if issues.count() > 0 and not recording.wrong_word:
                for issue in issues:
                    issue.status = "resolved"
                    issue.save(update_fields=["status"])
        logger.info(f"Ready with session {session.id}.")
