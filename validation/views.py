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
import json
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
    QueryDict,
)
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as django_login
from django.views.decorators.http import require_http_methods

from librecval.normalization import to_indexable_form

from .crude_views import *
from .models import Phrase, Recording, Speaker
from .helpers import get_distance_with_translations, perfect_match, exactly_one_analysis
from .forms import EditSegment, Login, Register


def index(request):
    """
    The home page.
    """
    is_linguist = user_is_linguist(request.user)
    is_community = user_is_community(request.user)

    all_class = "button button--success filter__button"
    new_class = "button button--success filter__button"
    linked_class = "button button--success filter__button"
    auto_validated_class = "button button--success filter__button"
    mode = request.GET.get("mode")

    if mode == "all":
        if is_linguist:
            all_phrases = Phrase.objects.all()
        else:
            all_phrases = Phrase.objects.filter(status="new")
        all_class = "button button--success filter__button filter__button--active"
    elif mode == "new":
        all_phrases = Phrase.objects.filter(status="new")
        new_class = "button button--success filter__button filter__button--active"
    elif mode == "linked":
        all_phrases = Phrase.objects.filter(status="linked")
        linked_class = "button button--success filter__button filter__button--active"
    elif mode == "auto-validated":
        all_phrases = Phrase.objects.filter(status="auto-validated")
        auto_validated_class = (
            "button button--success filter__button filter__button--active"
        )
    else:
        all_phrases = Phrase.objects.all()
        all_class = "button button--success filter__button filter__button--active"

    # The _segment_card needs a dictionary of recordings
    # in order to properly display search results
    # so we're just going to play nice with it here
    recordings = {}
    for phrase in all_phrases:
        recordings[phrase] = phrase.recordings

    paginator = Paginator(all_phrases, 5)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)
    auth = request.user.is_authenticated
    context = dict(
        phrases=phrases,
        recordings=recordings,
        all_class=all_class,
        new_class=new_class,
        linked_class=linked_class,
        auto_validated_class=auto_validated_class,
        auth=auth,
        is_linguist=is_linguist,
        is_community=is_community,
    )
    return render(request, "validation/list_phrases.html", context)


def search_phrases(request):
    """
    The search results for pages.
    """
    is_linguist = user_is_linguist(request.user)
    is_community = user_is_community(request.user)

    query = request.GET.get("query")
    cree_matches = Phrase.objects.filter(transcription__contains=query)
    english_matches = Phrase.objects.filter(translation__contains=query)
    all_matches = list(set().union(cree_matches, english_matches))
    all_matches.sort(key=lambda phrase: phrase.transcription)

    query_term = QueryDict("", mutable=True)
    query_term.update({"query": query})

    recordings = {}
    for phrase in all_matches:
        recordings[phrase] = [recording for recording in phrase.recordings]
    is_linguist = user_is_linguist(request.user)

    paginator = Paginator(all_matches, 5)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)
    context = dict(
        phrases=phrases,
        recordings=recordings,
        search_term=query,
        query=query_term,
        encode_query_with_page=encode_query_with_page,
        is_linguist=is_linguist,
        is_community=is_community,
        auth=request.user.is_authenticated,
    )
    return render(request, "validation/search.html", context)


def advanced_search(request):
    """
    The search results for pages.
    """
    query = Speaker.objects.all()
    speakers = [q.code for q in query]

    context = dict(
        speakers=speakers,
        auth=request.user.is_authenticated,
        is_linguist=user_is_linguist(request.user),
    )
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
    is_linguist = user_is_linguist(request.user)
    is_community = user_is_community(request.user)

    transcription = request.GET.get("transcription")
    translation = request.GET.get("translation")
    analysis = request.GET.get("analysis")
    status = request.GET.get("status")
    speakers = request.GET.getlist("speaker-options")
    quality = request.GET.get("quality")

    if transcription != "":
        cree_matches = Phrase.objects.filter(transcription__contains=transcription)
    else:
        cree_matches = []

    if translation != "":
        english_matches = Phrase.objects.filter(translation__contains=translation)
    else:
        english_matches = []

    # TODO: filter by analysis
    if analysis != "":
        analysis_matches = Phrase.objects.filter(analysis__contains=analysis)
    else:
        analysis_matches = []

    if transcription == "" and translation == "" and analysis == "":
        phrase_matches = Phrase.objects.all()
    else:
        phrase_matches = list(
            set().union(cree_matches, english_matches, analysis_matches)
        )

    if status != "all":
        if status == "new":
            status_matches = Phrase.objects.filter(status="new")
        elif status == "linked":
            status_matches = Phrase.objects.filter(status="linked")
        elif status == "auto-val":
            status_matches = Phrase.objects.filter(status="auto-validated")
        phrase_and_status_matches = list(
            set(phrase_matches).intersection(status_matches)
        )
    else:
        phrase_and_status_matches = phrase_matches

    recordings = {}
    all_matches = []
    for phrase in phrase_and_status_matches:
        recordings[phrase] = []
        if ("all" in speakers or speakers == []) and (quality == "all" or not quality):
            recordings[phrase] = list(phrase.recordings)
        else:
            for recording in phrase.recordings:
                if recording.speaker.code in speakers or recording.quality == quality:
                    recordings[phrase].append(recording)

        if recordings[phrase]:
            all_matches.append(phrase)

    all_matches.sort(key=lambda phrase: phrase.transcription)

    query = QueryDict("", mutable=True)
    query.update(
        {
            "transcription": transcription,
            "translation": translation,
            "analysis": analysis,
            "status": status,
        }
    )
    for speaker in speakers:
        query.appendlist("speaker-options", speaker)

    paginator = Paginator(all_matches, 5)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)
    context = dict(
        phrases=phrases,
        recordings=recordings,
        search_term="advanced search",
        query=query,
        encode_query_with_page=encode_query_with_page,
        is_linguist=is_linguist,
        is_community=is_community,
        auth=request.user.is_authenticated,
    )
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
            translation = form.cleaned_data["translation"]
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
    field_transcription = phrases[0].field_transcription
    suggestions = get_distance_with_translations(field_transcription)

    segment_name = phrases[0].transcription

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
            group = form.cleaned_data["role"]
            if not group:
                group = "Community"
            else:
                group = group.title()
            user = authenticate(request, username=username, password=password)
            if user is None:
                new_user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                new_user.save()
                group, _ = Group.objects.get_or_create(name=group)
                group.user_set.add(new_user)
                response = HttpResponseRedirect("/login")
                return response

    context = dict(form=form)
    return render(request, "validation/register.html", context)


# TODO: Speaker bio page like https://ojibwe.lib.umn.edu/about/voices


@require_http_methods(["POST"])
def record_translation_judgement(request, phrase_id):
    # TODO: check that user is logged in
    phrase = get_object_or_404(Phrase, id=phrase_id)
    judgement = json.loads(request.body)

    if judgement["judgement"] == "yes":
        phrase.validated = True
        phrase.status = "linked"
        phrase.modifier = str(request.user)
    elif judgement["judgement"] in ["no", "idk"]:
        phrase.validated = False
        phrase.status = "new"
        phrase.modifier = str(request.user)
    else:
        return HttpResponseBadRequest()

    phrase.save()
    return JsonResponse({"status": "ok"})


@require_http_methods(["POST"])
def record_audio_quality_judgement(request, recording_id):
    # TODO: check that user is logged in
    rec = get_object_or_404(Recording, id=recording_id)
    print(recording_id)
    judgement = json.loads(request.body)

    if judgement["judgement"] in ["good", "bad"]:
        rec.quality = judgement["judgement"]
    else:
        return HttpResponseBadRequest()

    rec.save()
    return JsonResponse({"status": "ok"})


def encode_query_with_page(query, page):
    query["page"] = page
    return f"?{query.urlencode()}"


def user_is_linguist(user):
    if user.is_authenticated:
        for g in user.groups.all():
            if g.name == "Linguist":
                return True

    return False


def user_is_community(user):
    if user.is_authenticated:
        for g in user.groups.all():
            if g.name == "Linguist" or g.name == "Community":
                return True

    return False
