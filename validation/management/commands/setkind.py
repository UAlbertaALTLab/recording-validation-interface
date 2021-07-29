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

    help = "determines if a Phrase object is a sentence or a word"

    def handle(self, *args, **options):
        pass
