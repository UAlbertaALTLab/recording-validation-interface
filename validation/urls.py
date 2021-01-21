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


from django.urls import path

from . import views

app_name = "validation"
urlpatterns = [
    path("", views.index, name="index"),
    # TODO: phrases/<int:phrases_id>/<slug>
    path("phrases", views.search_phrases, name="search_phrases"),
    path("phrases/<int:phrase_id>/", views.update_text, name="update_text"),
    path("recording/<str:recording_id>.m4a", views.serve_recording, name="recording"),
    path(
        "recording/_search/<str:query>",
        views.search_recordings,
        name="search_recordings",
    ),
    path("crude/sessions", views.list_all_sessions),
    path(
        "crude/sessions/<str:session_id>",
        views.all_recordings_for_session,
        name="crude_recordings",
    ),
    path("<str:segment_id>", views.segment_content_view, name="segment_detail"),
]
