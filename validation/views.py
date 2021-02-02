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

import io
from pathlib import Path
import datetime

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
    HttpResponseRedirect,
)
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as django_login

from librecval.normalization import to_indexable_form

from .crude_views import *
from .models import Phrase, Recording, Speaker
from .helpers import get_distance_with_translations
from .forms import EditSegment, Login, Register


def index(request):
    """
    The home page.
    """
    mode = query = request.GET.get("mode")
    if mode == "all":
        all_phrases = Phrase.objects.all()
    elif mode == "validated":
        all_phrases = Phrase.objects.filter(validated=True)
    elif mode == "unvalidated":
        all_phrases = Phrase.objects.filter(validated=False)
    else:
        all_phrases = Phrase.objects.all()

    paginator = Paginator(all_phrases, 30)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)
    auth = request.user.is_authenticated
    context = dict(phrases=phrases, auth=auth)
    return render(request, "validation/list_phrases.html", context)


def search_phrases(request):
    """
    The search results for pages.
    """
    query = request.GET.get("query")
    cree_matches = Phrase.objects.filter(transcription__contains=query)
    english_matches = Phrase.objects.filter(translation__contains=query)
    all_matches = list(set().union(cree_matches, english_matches))
    all_matches.sort(key=lambda phrase: phrase.transcription)
    paginator = Paginator(all_matches, 30)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)
    context = dict(phrases=phrases, search_term=query)
    return render(request, "validation/search.html", context)


def advanced_search(request):
    """
    The search results for pages.
    """
    query = Speaker.objects.all()
    speakers = [q.code for q in query]

    context = dict(speakers=speakers)
    return render(request, "validation/advanced_search.html", context)


def advanced_search_results(request):
    """
    Search results for advanced search
    Takes in parameters from GET request and makes necessary
    queries to return all the appropriate entries
    The steps are:
    cree phrases UNION english phrases UNION analysis
    INTERSECT status
    INTERSECT speaker
    """
    transcription = request.GET.get("transcription")
    translation = request.GET.get("translation")
    analysis = request.GET.get("analysis")
    status = request.GET.get("status")
    speakers = request.GET.getlist("speaker-options")

    if transcription != "":
        cree_matches = Phrase.objects.filter(transcription__contains=transcription)
    else:
        cree_matches = []

    if translation != "":
        english_matches = Phrase.objects.filter(translation__contains=translation)
    else:
        english_matches = []

    # TODO: filter by analysis

    if transcription == "" and translation == "":
        phrase_matches = Phrase.objects.all()
    else:
        phrase_matches = list(set().union(cree_matches, english_matches))

    if status != "all":
        if status == "validated":
            status_matches = Phrase.objects.filter(validated=True)
        elif status == "unvalidated":
            status_matches = Phrase.objects.filter(validated=False)
        phrase_and_status_matches = list(
            set(phrase_matches).intersection(status_matches)
        )
    else:
        phrase_and_status_matches = phrase_matches

    all_matches = []
    if "all" in speakers or speakers == []:
        all_matches = phrase_and_status_matches
    else:
        for phrase in phrase_and_status_matches:
            for recording in phrase.recordings:
                if recording.speaker.code in speakers:
                    all_matches.append(phrase)

    all_matches.sort(key=lambda phrase: phrase.transcription)

    paginator = Paginator(all_matches, 30)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)
    context = dict(phrases=phrases, search_term="advanced search")
    return render(request, "validation/search.html", context)


def update_text(request):
    """
    The search results for pages.
    """
    return HttpResponse(501)


def serve_recording(request, recording_id):
    """
    Serve a (transcoded) recording audio file.
    Note: To make things ~~WEB SCALE~~, we should NOT be doing this in Django;
    instead, Apache/Nginx should be doing this for us.
    """

    from media_with_range.views import serve_file

    # How many digits of the hash to include in the ETag.
    # Practically, we do not need to make the entire hash part of the etag;
    # just a part of it. Note: GitHub uses 7 digits.
    HASH_PREFIX_LENGTH = 7
    recording = get_object_or_404(Recording, id=recording_id)
    audio_dir = Recording.get_path_to_audio_directory()

    local_file_path = audio_dir / f"{recording.id}.m4a"
    response = serve_file(request, local_file_path)

    # The recording files basically never change, so tell everybody to cache
    # the dookey out these files (or at very least, a year).
    response["Cache-Control"] = f"public, max-age={60 * 60 * 24 * 365}"
    response["ETag"] = f'"{recording.id[:HASH_PREFIX_LENGTH]}"'
    return response


def search_recordings(request, query):
    """
    Searches for recordings whose phrase's transcription matches the query.
    The response is JSON that can be used by external apps (i.e., itwêwina).
    """

    # Maximum amount of comma-separated query terms.
    MAX_RECORDING_QUERY_TERMS = 3

    # Commas are fence posts: there will be one less comma than query terms.
    if query.count(",") >= MAX_RECORDING_QUERY_TERMS:
        response = JsonResponse((), safe=False)
        response.status_code = 414
        return add_cors_headers(response)

    word_forms = frozenset(query.split(","))

    def make_absolute_uri_for_recording(rec: Recording) -> str:
        uri = rec.compressed_audio.url
        if uri.startswith("/"):
            # It's a relative URI: build an absolute URI:
            return request.build_absolute_uri(uri)

        # It's an absolute URI already:
        assert uri.startswith("http")
        return uri

    def make_absolute_uri_for_speaker(code: str) -> str:
        return f"https://www.altlab.dev/maskwacis/Speakers/{code}.html"

    recordings = []
    for form in word_forms:
        # Assume the query is an SRO transcription; prepare it for a fuzzy match.
        fuzzy_transcription = to_indexable_form(form)
        result_set = Recording.objects.filter(
            phrase__fuzzy_transcription=fuzzy_transcription,
            speaker__gender__isnull=False,
        )

        recordings.extend(
            {
                "wordform": rec.phrase.transcription,
                "speaker": rec.speaker.code,
                "speaker_name": rec.speaker.full_name,
                "anonymous": rec.speaker.anonymous,
                "gender": rec.speaker.gender,
                "dialect": rec.speaker.dialect,
                "recording_url": make_absolute_uri_for_recording(rec),
                "speaker_bio_url": make_absolute_uri_for_speaker(rec.speaker.code),
            }
            for rec in result_set
        )

    response = JsonResponse(recordings, safe=False)

    if len(recordings) == 0:
        # No matches. Return an empty JSON response
        response.status_code = 404

    return add_cors_headers(response)


def add_cors_headers(response):
    """
    Adds appropriate Access-Control-* headers for cross-origin XHR responses.
    """
    response["Access-Control-Allow-Origin"] = "*"
    return response


def segment_content_view(request, segment_id):
    """
    The view for a single segment
    Returns the selected phrase and info provided by the helper functions
    """
    if request.method == "POST":
        form = EditSegment(request.POST)
        og_phrase = Phrase.objects.filter(id=segment_id)[0]
        phrase_id = og_phrase.id
        if form.is_valid():
            transcription = form.cleaned_data["cree"]
            translation = form.cleaned_data["transl"]
            analysis = form.cleaned_data["analysis"]
            p = Phrase.objects.filter(id=phrase_id)[0]
            p.transcription = transcription
            p.translation = translation
            p.analysis = analysis
            p.validated = True
            p.modifier = str(request.user)
            p.date = datetime.datetime.now()
            p.save()

    phrases = Phrase.objects.filter(id=segment_id)
    segment_name = phrases[0].transcription
    suggestions = get_distance_with_translations(segment_name)
    history = phrases[0].history.all()
    auth = request.user.is_authenticated

    form = EditSegment()

    context = dict(
        phrases=phrases,
        segment_name=segment_name,
        suggestions=suggestions,
        form=form,
        history=history,
        auth=auth,
    )

    return render(request, "validation/segment_details.html", context)


def register(request):
    """
    Serves the register page and creates a new user on success
    """
    form = Register(request.POST)

    if request.method == "POST":
        if form.is_valid():
            username = form.clean_username()
            password = form.cleaned_data["password"]
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            user = authenticate(request, username=username, password=password)
            if user is None:
                new_user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                new_user.save()
                response = HttpResponseRedirect("/login")
                return response

    context = dict(form=form)
    return render(request, "validation/register.html", context)


# TODO: Speaker bio page like https://ojibwe.lib.umn.edu/about/voices
