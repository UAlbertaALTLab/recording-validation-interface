#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright (C) 2018 Eddie Antonio Santos <easantos@ualberta.ca>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Reindexes phrases (transcriptions, translations) for search.

Usage:

    python manage.py reindexphrases
"""

from django.core.management.base import BaseCommand  # type: ignore

from validation.models import Phrase


class Command(BaseCommand):
    help = "reindexes all phrases in the database"

    def add_arguments(self, parser):
        # No arguments needed.
        pass

    def handle(self, *args, **options) -> None:
        # This is really dumb: basically, the indexed form is ALWAYS recreated
        # .save(). So... we'll fetch every single item, and call its .save()
        # method. It's silly, but it works!
        phrases = Phrase.objects.all()
        default = Phrase._meta.get_field("fuzzy_transcription").get_default()
        for phrase in phrases:
            phrase.save()
            assert phrase.fuzzy_transcription != default
