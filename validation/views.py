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

import datetime
import io
import json
import operator
from functools import reduce
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
    QueryDict,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as django_login
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from librecval.normalization import to_indexable_form

from .crude_views import *
from .models import Phrase, Recording, Speaker, RecordingSession, Issue
from .helpers import get_distance_with_translations, perfect_match, exactly_one_analysis
from .forms import EditSegment, Login, Register, FlagSegment


def index(request):
    """
    The home page.
    """

    is_linguist = user_is_linguist(request.user)
    is_expert = user_is_expert(request.user)

    mode = request.GET.get("mode")

    if mode == "all" or not mode:
        if is_linguist:
            all_phrases = Phrase.objects.all()
        else:
            all_phrases = Phrase.objects.exclude(origin="MD").exclude(
                status="auto-validated"
            )
    else:
        all_phrases = Phrase.objects.filter(status=mode)

    all_phrases = all_phrases.prefetch_related("recording_set__speaker")

    sessions = RecordingSession.objects.order_by("id").values("id", "date").distinct()
    session = request.GET.get("session")
    if session != "all" and session:
        session_date = datetime.datetime.strptime(session, "%Y-%m-%d").date()
        all_phrases = all_phrases.filter(
            recording__session__date=session_date
        ).distinct()

    all_phrases = all_phrases.order_by("transcription")

    paginator = Paginator(all_phrases, 5)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)

    query_term = QueryDict("", mutable=True)
    if session:
        query_term.update({"session": session})
    if mode:
        query_term.update({"mode": mode})

    if not mode:
        mode = "all"

    if not session or session == "all":
        session = "all sessions"

    recordings, forms = prep_phrase_data(request, phrases)

    if request.method == "POST":
        form = forms.get(int(request.POST.get("phrase_id")), None)
        if form is not None:
            if form.is_valid():
                save_issue(form.cleaned_data, request.user)

    auth = request.user.is_authenticated
    context = dict(
        phrases=phrases,
        recordings=recordings,
        auth=auth,
        is_linguist=is_linguist,
        is_expert=is_expert,
        forms=forms,
        sessions=sessions,
        query=query_term,
        session=session,
        mode=mode,
        encode_query_with_page=encode_query_with_page,
    )
    return render(request, "validation/list_phrases.html", context)


def search_phrases(request):
    """
    The search results for pages.
    """
    is_linguist = user_is_linguist(request.user)
    is_expert = user_is_expert(request.user)

    query = request.GET.get("query")
    all_matches = Phrase.objects.filter(
        Q(transcription__contains=query) | Q(translation__contains=query)
    ).prefetch_related("recording_set__speaker")
    all_matches = list(all_matches)
    all_matches.sort(key=lambda phrase: phrase.transcription)

    query_term = QueryDict("", mutable=True)
    query_term.update({"query": query})

    paginator = Paginator(all_matches, 5)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)

    recordings, forms = prep_phrase_data(request, phrases)

    if request.method == "POST":
        form = forms.get(int(request.POST.get("phrase_id")), None)
        if form is not None:
            if form.is_valid():
                save_issue(form.cleaned_data, request.user)

    context = dict(
        phrases=phrases,
        recordings=recordings,
        search_term=query,
        query=query_term,
        encode_query_with_page=encode_query_with_page,
        is_linguist=is_linguist,
        is_expert=is_expert,
        forms=forms,
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
    is_expert = user_is_expert(request.user)

    transcription = request.GET.get("transcription")
    translation = request.GET.get("translation")
    analysis = request.GET.get("analysis")
    status = request.GET.get("status")
    speakers = request.GET.getlist("speaker-options")
    quality = request.GET.get("quality")

    filter_query = []
    if transcription:
        filter_query.append(Q(transcription__contains=transcription))
    if translation:
        filter_query.append(Q(translation__contains=translation))
    if analysis:
        filter_query.append(Q(analysis__contains=analysis))
    if status and status != "all":
        filter_query.append(Q(status=status))

    if filter_query:
        phrase_matches = Phrase.objects.filter(
            reduce(operator.or_, filter_query)
        ).prefetch_related("recording_set__speaker")
    else:
        phrase_matches = Phrase.objects.all().prefetch_related("recording_set__speaker")

    recordings = {}
    all_matches = []

    # We use the negation of the query, ~Q, and .exclude here
    # because we want to remove any entries and recordings that do not match
    # the criteria, which cannot be accomplished with .filter
    recordings_exclude_query = []
    if speakers and "all" not in speakers:
        recordings_exclude_query.append(~Q(speaker__in=speakers))
    if quality and "all" not in quality:
        recordings_exclude_query.append(~Q(quality__in=quality))

    for phrase in phrase_matches:
        if recordings_exclude_query:
            recordings[phrase] = phrase.recordings.exclude(
                reduce(operator.and_, recordings_exclude_query)
            )
        else:
            recordings[phrase] = list(phrase.recordings)
        if recordings[phrase]:
            all_matches.append(phrase)

    all_matches.sort(key=lambda phrase: phrase.transcription)
    _, forms = prep_phrase_data(request, all_matches)

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
        is_expert=is_expert,
        forms=forms,
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
        # No bad recordings!
        result_set = result_set.exclude(quality=Recording.BAD)

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


@login_required()
@require_http_methods(["POST"])
def record_translation_judgement(request, phrase_id):
    phrase = get_object_or_404(Phrase, id=phrase_id)
    judgement = json.loads(request.body)

    if judgement["judgement"] == "yes":
        phrase.validated = True
        phrase.status = "linked"
        phrase.modifier = str(request.user)
        phrase.date = datetime.datetime.now()
    elif judgement["judgement"] in ["no", "idk"]:
        phrase.validated = False
        phrase.status = "new"
        phrase.modifier = str(request.user)
        phrase.date = datetime.datetime.now()
    else:
        return HttpResponseBadRequest()

    phrase.save()
    return JsonResponse({"status": "ok"})


@login_required()
@require_http_methods(["POST"])
def record_audio_quality_judgement(request, recording_id):
    rec = get_object_or_404(Recording, id=recording_id)
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
    return user.groups.filter(name="Linguist").exists()


def user_is_expert(user):
    return user.groups.filter(name__in=["Linguist", "Expert"]).exists()


def prep_phrase_data(request, phrases):
    # The _segment_card needs a dictionary of recordings
    # in order to properly display search results
    recordings = {}
    forms = {}
    for phrase in phrases:
        recordings[phrase] = phrase.recordings
        if request.method == "POST" and int(request.POST.get("phrase_id")) == phrase.id:
            forms[phrase.id] = FlagSegment(
                request.POST, initial={"phrase_id": phrase.id}
            )
        else:
            forms[phrase.id] = FlagSegment(initial={"phrase_id": phrase.id})

    return recordings, forms


def save_issue(data, user):
    phrase_id = data["phrase_id"]
    issues = data["issues"]
    other_reason = data["other_reason"]
    comment = data["comment"]

    phrase = Phrase.objects.get(id=phrase_id)

    new_issue = Issue(
        phrase=phrase,
        other="other" in issues,
        bad_cree="bad_cree" in issues,
        bad_english="bad_english" in issues,
        bad_recording="bad_rec" in issues,
        comment=comment,
        other_reason=other_reason,
        created_by=user,
        created_on=datetime.datetime.now(),
    )

    new_issue.save()
