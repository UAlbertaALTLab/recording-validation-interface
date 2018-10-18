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

from django.db import models

from librecval.recording_session import SessionID, TimeOfDay, Location


def choices_from_enum(enum_class):
    """
    Utility for converting a Python 3.4+ Enum into a choices for a Django
    model. Retuns a dictionary suitable for using as keyword arguments for a
    CharField.
    """
    choices = tuple((x.value, x.value) for x in enum_class)
    max_length = max(len(x.value) for x in enum_class)
    return dict(max_length=max_length, choices=choices)


class RecordingSession(models.Model):
    """
    A session during which a number of recordings were made.

    Example sessions:

    2017-11-01-AM-OFF-_:
        Happended on the morning of November 1, 2017 in the office.
    """

    # See librecval for the appropriate choices:

    date = models.DateField(help_text="The day the session occured.")
    time_of_day = models.CharField(help_text="The time of day the session occured. May be empty.",
                                   blank=True, default='',
                                   **choices_from_enum(TimeOfDay))
    location = models.CharField(help_text="The location of the recordings. May be empty.",
                                blank=True, default='',
                                **choices_from_enum(Location))
    subsession = models.IntegerField(help_text="The 'subsession' number, if applicable.",
                                     null=True, blank=True)

    @classmethod
    def create_from(cls, session_id):
        """
        Create the model from the internal data class.
        """
        return cls(date=session_id.date,
                   time_of_day=session_id.time_of_day.value,
                   location=session_id.location.value,
                   subsession=session_id.subsession)

    def as_session_id(self):
        return SessionID(date=self.date,
                         # `and` prevents calling .parse() on a None value.
                         time_of_day=self.time_of_day and TimeOfDay.parse(self.time_of_day),
                         location=self.location and Location.parse(self.location),
                         subsession=self.subsession)
