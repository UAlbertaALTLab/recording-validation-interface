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
Django management command to download the recording metadata.

Its defaults are configured using the following settings:

    RECVAL_METADATA_PATH

See recvalsite/settings.py for more information.
"""

from pathlib import Path

import logme  # type: ignore

from django.conf import settings  # type: ignore
from django.core.management.base import BaseCommand  # type: ignore

from librecval.download_metadata import download_metadata


class Command(BaseCommand):
    help = "downloads the recordings metadata file from Google Drive"

    def add_arguments(self, parser):
        # No arguments needed.
        pass

    def handle(self, *args, **options) -> None:
        download_metadata(destination=settings.RECVAL_METADATA_PATH)
        self.stdout.write('Succesfully downloaded metadata!')
