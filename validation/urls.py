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
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

from . import views

app_name = "validation"
urlpatterns = [
    path("<str:language>/entries", views.entries, name="entries"),
    path(
        "",
        views.home,
        name="home",
    ),
    path(
        "login",
        auth_views.LoginView.as_view(template_name="validation/login.html"),
        name="login",
    ),
    path(
        "logout",
        auth_views.LogoutView.as_view(template_name="validation/logout.html"),
        name="logout",
    ),
    path("register", views.register, name="register"),
    # TODO: phrases/<int:phrases_id>/<slug>
    path("<str:language>/search/", views.search_phrases, name="search_phrases"),
    path(
        "<str:language>/advanced_search/", views.advanced_search, name="advanced_search"
    ),
    path(
        "<str:language>/advanced_search_results/",
        views.advanced_search_results,
        name="advanced_search_results",
    ),
    path(
        "<str:language>/phrases/<int:phrase_id>/", views.update_text, name="update_text"
    ),
    path("recording/<str:recording_id>.m4a", views.serve_recording, name="recording"),
    path(
        "recording/_search/<str:query>",
        views.search_recordings,
        name="search_recordings",
    ),
    path(
        "<str:language>/segment/<str:segment_id>",
        views.segment_content_view,
        name="segment_detail",
    ),
    path("<str:language>/issues", views.view_issues, name="issues"),
    path(
        "<str:language>/issues/<int:issue_id>",
        views.view_issue_detail,
        name="issue_detail",
    ),
    path(
        "<str:language>/speakers/<str:speaker_code>",
        views.speaker_view,
        name="speaker_view",
    ),
    path("<str:language>/speakers/", views.all_speakers, name="all_speakers"),
    path("<str:language>/record_audio", views.record_audio, name="record_audio"),
    path(
        "<str:language>/record_audio_from_entry/<str:phrase>",
        views.record_audio_from_entry,
        name="record_audio_from_entry",
    ),
    path(
        "api/record_translation_judgement/<int:phrase_id>",
        views.record_translation_judgement,
        name="record_translation_judgement",
    ),
    path(
        "api/record_audio_quality_judgement/<str:recording_id>",
        views.record_audio_quality_judgement,
        name="record_audio_quality_judgement",
    ),
    path(
        "api/record_audio_is_best/<str:recording_id>",
        views.record_audio_is_best,
        name="record_audio_is_best",
    ),
    path(
        "api/approve_user_phrase/<str:phrase_id>",
        views.approve_user_phrase,
        name="approve_user_phrase",
    ),
    path(
        "<str:language>/api/save_wrong_speaker_code/<str:recording_id>",
        views.save_wrong_speaker_code,
        name="save_wrong_speaker_code",
    ),
    path(
        "<str:language>/api/save_wrong_word/<str:recording_id>",
        views.save_wrong_word,
        name="save_wrong_word",
    ),
    path(
        "<str:language>/api/close_issue/<str:issue_id>",
        views.close_issue,
        name="close_issue",
    ),
    path(
        "<str:language>/api/bulk_search",
        views.bulk_search_recordings,
        name="bulk_search_recordings",
    ),
    path(
        "api/set_language/<str:language_code>", views.set_language, name="set_language"
    ),
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="validation/robots.txt", content_type="text/plain"
        ),
    ),
]
