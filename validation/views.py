#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import datetime
import json
import operator

# Copyright (C) 2018 Eddie Antonio Santos <easantos@ualberta.ca>,
#               2024 Felipe Banados Schwerter <banadoss@ualberta.ca>
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
import subprocess
import time
import re
from functools import reduce
from hashlib import sha256
from http import HTTPStatus
from pathlib import Path
from collections import Counter
from django.db import transaction

import mutagen as mutagen
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.mail import mail_admins
from django.contrib.auth import login as django_login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.paginator import Paginator
from django.db.models import Q, QuerySet, Count, Case, When, IntegerField, F
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
    QueryDict,
    HttpRequest,
)
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied

from librecval.normalization import to_indexable_form
from librecval.recording_session import SessionID
from .jinja2 import url

from .models import (
    Phrase,
    Recording,
    Speaker,
    RecordingSession,
    Issue,
    LanguageVariant,
    SemanticClass,
    SemanticClassAnnotation,
    HistoricalSemanticClassAnnotation,
    HistoricalRecording,
    HistoricalPhrase,
)
from .forms import (
    EditSegment,
    Register,
    FlagSegment,
    EditIssueWithRecording,
    EditIssueWithPhrase,
    RecordNewPhrase,
)
from .helpers import (
    get_distance_with_translations,
)
from .crk_sort import custom_sort


class UserRoles:
    def __init__(self, user=None, lang=None):
        self.is_linguist = (
            user
            and user.groups.filter(name="Linguist").exists()
            and user.groups.filter(name=lang).exists()
        )
        self.is_expert = (
            user
            and user.groups.filter(name__in=["Linguist", "Expert"]).exists()
            and user.groups.filter(name=lang).exists()
        )
        self.is_admin = user and user.is_superuser
        self.is_manager = (
            user
            and user.groups.filter(name="Manager").exists()
            and user.groups.filter(name=lang).exists()
        ) or self.is_admin


def home(request):
    """
    The home page that lets you select a language variant
    """
    languages = LanguageVariant.objects.all()
    auth = request.user.is_authenticated
    language_dict = {}
    no_lang_family = []

    for language in languages:
        if language.language_family:
            if language.language_family not in language_dict:
                language_dict[language.language_family] = [language]
            else:
                language_dict[language.language_family].append(language)
        else:
            no_lang_family.append(language)

    if no_lang_family:
        language_dict["All"] = no_lang_family

    context = dict(
        languages=language_dict,
        language=None,
        auth=auth,
        roles=UserRoles(request.user, None),
    )
    return render(request, "validation/home.html", context)


class RecvalLoginView(LoginView):
    template_name = "validation/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"roles": UserRoles()})
        return context


class RecvalLogoutView(LogoutView):
    template_name = "validation/logout.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"roles": UserRoles()})
        return context


@transaction.atomic
def update_phrase_order(all_phrases):
    # Create a dictionary to store the order of phrases
    phrase_order = {phrase.id: index for index, phrase in enumerate(all_phrases)}

    # Use a single database query to update the order of all phrases
    for phrase_id, new_order in phrase_order.items():
        Phrase.objects.filter(pk=phrase_id).update(display_order=new_order)

    # Retrieve the updated instances in the original order
    sorted_updated_phrases = sorted(all_phrases, key=lambda x: phrase_order[x.id])

    return sorted_updated_phrases


def semantic_classes_collect(semantic_classes):
    base_data = {
        str(x): {"phrases": x.phrases, "hyponyms": [str(y) for y in x.hyponyms.all()]}
        for x in semantic_classes
    }
    data = dict()

    def process(element):
        if element not in data:
            if len(base_data[element]["hyponyms"]) == 0:
                data[element] = base_data[element]["phrases"]
            for hyponym in base_data[element]["hyponyms"]:
                process(hyponym)
        data[element] = base_data[element]["phrases"] + sum(
            [data[x] for x in base_data[element]["hyponyms"]]
        )

    for element in base_data.keys():
        process(element)

    def build_dict(name, total_phrases, phrases):
        rest = f", ↪︎{total_phrases}" if phrases != total_phrases else ""
        return {
            "name": name,
            "total_phrases": total_phrases,
            "phrases": phrases,
            "entries": f"({phrases} entries{rest})",
        }

    return [
        build_dict(key, value, base_data[key]["phrases"]) for key, value in data.items()
    ]


def entries(request, language):
    """
    The main page.
    """
    roles = UserRoles(request.user, language)

    # Only show selected language
    language_object = get_language_object(language)
    all_phrases = Phrase.objects.filter(language=language_object)
    if (not language == "stoney-alexis") or user_has_alexis_permissions(request.user):
        language_sessions = (
            Recording.objects.filter(phrase_id__in=all_phrases)
            .values("session")
            .distinct()
        )
        language_sessions = [i["session"] for i in language_sessions]
        language_sessions = RecordingSession.objects.filter(id__in=language_sessions)

        mode = request.GET.get("mode")
        mode_options = {
            "auto-standardized": Phrase.AUTO,
            "new": Phrase.NEW,
            "linked": Phrase.LINKED,
            "user-submitted": Phrase.USER,
        }
        if mode and mode != "all":
            mode = mode_options[mode]

        if mode == "all" or not mode:
            all_phrases = all_phrases.exclude(status=Phrase.USER)
        else:
            all_phrases = all_phrases.filter(status=mode)

        all_phrases = all_phrases.prefetch_related("recording_set__speaker")

        sessions = (
            RecordingSession.objects.order_by("id").values("id", "date").distinct()
        )
        session = request.GET.get("session")
        if session != "all" and session:
            all_phrases = all_phrases.filter(recording__session__id=session).distinct()

        semantic = request.GET.get("semantic_class")
        hyponyms = request.GET.get("hyponyms")
        sorted_phrases = request.GET.get("sorted_phrases")

        if semantic:
            semantic_object = SemanticClass.objects.get(classification=semantic)
            if hyponyms == "checked":
                all_phrases = all_phrases.filter(
                    Q(semantic_classes__hypernyms=semantic_object)
                    | Q(semantic_classes=semantic_object)
                ).distinct()
            else:
                all_phrases = all_phrases.filter(semantic_classes=semantic_object)

        if language in ["maskwacis", "moswacihk"]:
            # step 3:
            if sorted_phrases == "checked":
                all_phrases = custom_sort(all_phrases)
                sorted_updated_phrases = update_phrase_order(all_phrases)
                all_phrases = sorted_updated_phrases

            else:
                # all_phrases = custom_sort(all_phrases)
                # sorted_updated_phrases = update_phrase_order(all_phrases)
                # all_phrases = sorted_updated_phrases

                # 2nd Step
                all_phrases = all_phrases.order_by("display_order")

        else:
            # If language is not in the specified list, order by transcription
            all_phrases = all_phrases.order_by("transcription")

    else:
        all_phrases = []
        session = None
        mode = None
        semantic = None
        language_sessions = []

    paginator = Paginator(all_phrases, 5)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)

    query_term = QueryDict("", mutable=True)
    if session:
        query_term.update({"session": session})
    if mode:
        query_term.update({"mode": mode})
    if semantic:
        query_term.update({"semantic_class": semantic})
    if hyponyms:
        query_term.update({"hyponyms": hyponyms})

    if not mode:
        mode = "all"

    if not session or session == "all":
        session = "all sessions"

    if semantic:
        semantic_display = f"relating to semantic class {semantic}"
    else:
        semantic_display = ""

    all_semantic_classes = semantic_classes_collect(
        SemanticClass.objects.distinct().annotate(
            phrases=Count(
                "phrase", distinct=True, filter=Q(phrase__language=language_object)
            ),
        )
    )
    all_semantic_classes.sort(key=lambda x: x["name"])

    recordings, forms = prep_phrase_data(request, phrases, language_object.name)

    speakers = language_object.speaker_set.all()

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
        roles=roles,
        forms=forms,
        sessions=language_sessions,
        speakers=speakers,
        query=query_term,
        session=session,
        mode=mode,
        semantic_display=semantic_display,
        all_semantic_classes=all_semantic_classes,
        semantic=semantic,
        encode_query_with_page=encode_query_with_page,
        language=language_object,
    )
    return render(request, "validation/list_phrases.html", context)


def search_phrases(request, language):
    """
    The search results for pages.
    """
    roles = UserRoles(request.user, language)
    language_object = get_language_object(language)

    query = request.GET.get("query")
    all_matches = (
        Phrase.objects.filter(
            Q(transcription__contains=query)
            | Q(fuzzy_transcription__contains=to_indexable_form(query))
            | Q(translation__contains=query)
        )
        .exclude(status=Phrase.USER)
        .filter(language=language_object)
        .prefetch_related("recording_set__speaker")
    )
    all_matches = list(all_matches)
    all_matches.sort(key=lambda phrase: phrase.transcription)

    query_term = QueryDict("", mutable=True)
    query_term.update({"query": query})

    paginator = Paginator(all_matches, 5)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)

    recordings, forms = prep_phrase_data(request, phrases, language_object.name)

    speakers = language_object.speaker_set.all()

    if request.method == "POST":
        form = forms.get(int(request.POST.get("phrase_id")), None)
        if form is not None:
            if form.is_valid():
                save_issue(form.cleaned_data, request.user)

    context = dict(
        phrases=phrases,
        recordings=recordings,
        speakers=speakers,
        search_term=query,
        query=query_term,
        encode_query_with_page=encode_query_with_page,
        roles=roles,
        forms=forms,
        auth=request.user.is_authenticated,
        language=language_object,
    )
    return render(request, "validation/search.html", context)


def advanced_search(request, language):
    """
    The search results for pages.
    """
    language_object = get_language_object(language)
    speakers = language_object.speaker_set.all()
    speakers = [speaker.code for speaker in speakers if speaker.recording_set.exists()]
    semantic_classes = (
        SemanticClass.objects.filter(phrase__language=language_object)
        .distinct()
        .order_by("classification")
    )

    context = dict(
        speakers=speakers,
        auth=request.user.is_authenticated,
        roles=UserRoles(request.user, language),
        language=language_object,
        semantic_classes=semantic_classes,
        semantic_class_sources=SemanticClassAnnotation.SOURCE_CHOICES,
    )
    return render(request, "validation/advanced_search.html", context)


def advanced_search_results(request, language):
    """
    Search results for advanced search
    Takes in parameters from GET request and makes necessary
    queries to return all the appropriate entries
    The steps are:
    target language phrases UNION english phrases UNION analysis
    INTERSECT status
    INTERSECT speaker
    """
    roles = UserRoles(request.user, language)

    transcription = request.GET.get("transcription")
    if transcription:
        transcription = transcription.strip()
    translation = request.GET.get("translation")
    if translation:
        translation = translation.strip()
    exact = request.GET.get("exact")
    analysis = request.GET.get("analysis")
    lemma = request.GET.get("lemma")
    if lemma:
        lemma = lemma.strip()
    kind = request.GET.get("kind")
    status = request.GET.get("status")
    status_choice = status
    semantic = request.GET.get("semantic_class")
    semantic_class_source = request.GET.get("semantic-class-source", "all")
    speakers = request.GET.getlist("speaker-options")
    quality = request.GET.getlist("quality")
    language_object = get_language_object(language)

    if status and status != "all":
        status_choices = {
            "new": Phrase.NEW,
            "linked": Phrase.LINKED,
            "auto-validated": Phrase.AUTO,
            "user-submitted": Phrase.USER,
            "needs-review": Phrase.REVIEW,
            "not-checked": "not-checked",
            "grey-card": "grey-card",
        }
        status = status_choices[status]

    filter_query = []
    if transcription:
        if exact == "exact":
            filter_query.append(Q(transcription=transcription))
        else:
            filter_query.append(
                Q(fuzzy_transcription__contains=to_indexable_form(transcription))
            )
            filter_query.append(Q(transcription__contains=transcription))
    if translation:
        filter_query.append(Q(translation__contains=translation))
    if analysis:
        filter_query.append(Q(analysis__contains=analysis))
    if lemma:
        filter_query.append(Q(analysis__contains=lemma))
    if status:
        if status == "not-checked":
            filter_query.append(
                Q(status=Phrase.NEW) | Q(status=Phrase.AUTO) | Q(status=Phrase.USER)
            )
        elif status == "grey-card":
            filter_query.append(~Q(validated=True) & ~Q(status=Phrase.REVIEW))
        elif status != "all":
            filter_query.append(Q(status=status))
    if semantic:
        semantic_object = SemanticClass.objects.get(classification=semantic)
        filter_query.append(Q(semantic_classes=semantic_object))
    if semantic_class_source and semantic_class_source != "all":
        annotations = SemanticClassAnnotation.objects.filter(
            source=semantic_class_source
        ).values("phrase")
        filter_query.append(Q(id__in=annotations))

    if kind and kind != "all":
        filter_kind = Phrase.WORD if kind == "word" else Phrase.SENTENCE
        filter_query.append(Q(kind=filter_kind))

    if filter_query:
        phrase_matches = (
            Phrase.objects.filter(language=language_object)
            .filter(reduce(operator.or_, filter_query))
            .prefetch_related("recording_set__speaker")
        )
    else:
        phrase_matches = Phrase.objects.filter(
            language=language_object
        ).prefetch_related("recording_set__speaker")

    recordings = {}
    all_matches = []

    # Performing the filtering directly on the database (by using django querysets)
    # is much faster than doing it in Python.

    recordings_include_query = None
    phrase_include_query = None
    if speakers and "all" not in speakers:
        recordings_include_query = Q(speaker__in=speakers)
        phrase_include_query = Q(recording__speaker__in=speakers)
    if quality and "all" not in quality:
        quality_recording_filter = Q(quality__in=quality)
        quality_phrase_filter = Q(recording__quality__in=quality)
        recordings_include_query = (
            quality_recording_filter
            if not recordings_include_query
            else recordings_include_query & quality_recording_filter
        )
        phrase_include_query = (
            quality_phrase_filter
            if not phrase_include_query
            else phrase_include_query & quality_phrase_filter
        )

    all_matches = (
        phrase_matches
        if not phrase_include_query
        else phrase_matches.filter(phrase_include_query)
    )
    all_matches = all_matches.order_by("transcription").distinct()
    for phrase in all_matches:
        recordings[phrase] = (
            phrase.recording_set.all()
            if not recordings_include_query
            else phrase.recording_set.filter(recordings_include_query)
        )

    _, forms = prep_phrase_data(request, all_matches, language_object.name)

    query = QueryDict("", mutable=True)
    query.update(
        {
            "transcription": transcription,
            "translation": translation,
            "analysis": analysis,
            "status": status_choice,
            "kind": kind,
            "semantic": semantic,
            "exact": exact,
            "lemma": lemma,
            "quality": quality,
            "semantic_class": semantic,
            "semantic-class-source": semantic_class_source,
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
        roles=roles,
        forms=forms,
        auth=request.user.is_authenticated,
        language=language_object,
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


def annotate_relaxed_wordform(data, desired_wordform):
    recorded_wordform = data["wordform"]
    data["wordform"] = desired_wordform
    data["recorded_wordform"] = recorded_wordform
    return data


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

    recordings = []
    for form in word_forms:
        # Assume the query is an SRO transcription; prepare it for a fuzzy match.
        fuzzy_transcription = to_indexable_form(form)
        all_matches = Recording.objects.filter(
            phrase__fuzzy_transcription=fuzzy_transcription,
        )
        results = exclude_known_bad_recordings(all_matches)

        recordings.extend(recording.as_json(request) for recording in results)

    response = JsonResponse(recordings, safe=False)

    if len(recordings) == 0:
        # No matches. Return an empty JSON response
        response.status_code = 404

    return add_cors_headers(response)


def regex_from_equivalences(term, equivalences):
    str = r"^{}$".format(term)
    for equivalence in equivalences:
        str = re.sub(equivalence, equivalence, str)
    return str


def extract_recording_sample(sample):
    if sample.count() <= 10:
        return sample
    by_speaker = [
        list(sample.filter(speaker=s["speaker"]))
        for s in sample.values("speaker").distinct()
    ]
    answer = set(sample.filter(is_best=True))
    while len(answer) < 10:
        for speaker_list in by_speaker:
            try:
                answer.add(speaker_list.pop(0))
            except IndexError:
                pass
    return list(answer)


def bulk_search_recordings(request: HttpRequest, language: str):
    """
    API endpoint to retrieve EXACT wordforms and return the URLs and metadata for the recordings.

    Oct 2024 API CHANGE:  The API now is expected to retrieve RELAXED wordforms, not EXACT
                          UNLESS also given the exact=true parameter.

    Example: /maskwacis/api/bulk_search?q=mistik&q=minahik&q=waskay&q=mîtos&q=mistikow&q=mêstan&exact=true
    """

    query_terms = request.GET.getlist("q")
    matched_recordings = []
    not_found = []
    exact = request.GET.get("exact", default=None) == "true"
    relaxed_equivalences = [
        r"(y|ý)",
        r"(á|à|â|ā)",
        r"(í|ì|î|ī)",
        r"(ó|ò|ô|ō)",
        r"(e|é|è|ê|ē)",
    ]

    if not LanguageVariant.objects.filter(code=language).exists():
        not_found = [term for term in query_terms]
        response = {"matched_recordings": matched_recordings, "not_found": not_found}
        json_response = JsonResponse(response)
        return add_cors_headers(json_response)

    for term in query_terms:
        language_object = get_language_object(language)
        if exact:
            all_matches = Recording.objects.filter(
                phrase__transcription=term, phrase__language=language_object
            )
        else:
            all_matches = Recording.objects.filter(
                phrase__transcription__iregex=regex_from_equivalences(
                    term, relaxed_equivalences
                ),
                phrase__language=language_object,
            )
        results = exclude_known_bad_recordings(all_matches)
        if not exact:
            # We will reuse the exact keyword for a full query.
            # The advantage of this is that, because morphodict queries do not ask for an exact query,
            # It will automatically limit requests coming from morphodict.
            results = extract_recording_sample(results)
        if results:
            matched_recordings.extend(
                annotate_relaxed_wordform(recording.as_json(request), term)
                for recording in results
            )
        else:
            not_found.append(term)

    if matched_recordings:
        matched_recordings.sort(
            key=lambda recording: not recording.get("is_best")
        )  # Without not, it places the best at the end.

    response = {"matched_recordings": matched_recordings, "not_found": not_found}

    json_response = JsonResponse(response)

    return add_cors_headers(json_response)


def add_cors_headers(response):
    """
    Adds appropriate Access-Control-* headers for cross-origin XHR responses.
    """
    response["Access-Control-Allow-Origin"] = "*"
    return response


@login_required()
def segment_content_view(request, language, segment_id):
    """
    The view for a single segment
    Returns the selected phrase and info provided by the helper functions
    """
    language_object = get_language_object(language)
    if request.method == "POST":
        form = EditSegment(request.POST)
        og_phrase = Phrase.objects.get(id=segment_id, language=language_object)
        phrase_id = og_phrase.id
        if form.is_valid():
            transcription = (
                form.cleaned_data["source_language"].strip() or og_phrase.transcription
            )
            translation = (
                form.cleaned_data["translation"].strip() or og_phrase.translation
            )
            analysis = form.cleaned_data["analysis"].strip() or og_phrase.analysis
            comment = form.cleaned_data["comment"].strip() or og_phrase.comment
            rapidwords = form.cleaned_data["rapidwords"]
            p = Phrase.objects.get(id=phrase_id, language=language_object)
            previous_classes = SemanticClassAnnotation.objects.filter(
                phrase=p, semantic_class__collection=SemanticClass.RW
            )
            for candidate in previous_classes:
                if candidate.semantic_class not in rapidwords:
                    candidate.delete()
            previous_classes = p.semantic_classes.all()
            for candidate in rapidwords:
                if candidate not in previous_classes:
                    SemanticClassAnnotation.objects.create(
                        phrase=p,
                        semantic_class=candidate,
                        source=SemanticClassAnnotation.MANUAL,
                    )
            p.transcription = transcription
            p.translation = translation
            p.analysis = analysis
            p.comment = comment
            p.validated = True
            p.modifier = str(request.user)
            p.date = datetime.datetime.now()
            p.save()

    phrase = Phrase.objects.get(id=segment_id, language=language_object)
    _transcription = phrase.field_transcription or phrase.transcription
    suggestions = {}

    # Only try to collect suggestions if the right cookie is set.
    # Otherwise continue.
    if request.COOKIES.get("suggestions", "on") != "off":
        suggestions = get_distance_with_translations(_transcription)

    segment_name = phrase.transcription

    history = phrase.history.all()
    rapidwords_history = HistoricalSemanticClassAnnotation.objects.filter(
        phrase=phrase, semantic_class__collection="rapidwords"
    )
    auth = request.user.is_authenticated

    form = EditSegment(
        initial={
            "source_language": phrase.transcription,
            "translation": phrase.translation,
            "analysis": phrase.analysis,
            "comment": phrase.comment,
            "stem": phrase.stem,
            "lexical_category": phrase.lexical_category,
            "rapidwords": phrase.semantic_classes.all(),
        }
    )

    context = dict(
        phrase=phrase,
        segment_name=segment_name,
        suggestions=suggestions,
        form=form,
        history=history,
        rw_history=rapidwords_history,
        auth=auth,
        roles=UserRoles(request.user, language),
        language=language_object,
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
            email = form.cleaned_data["email"]
            group = form.cleaned_data["role"]
            languages = form.cleaned_data["language_variant"]
            if not group:
                group = "Learner"
            else:
                group = group.title()
            user = authenticate(request, username=username, password=password)
            if user is None:
                new_user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                )
                new_user.save()
                if group == "Linguist" or group == "Expert":
                    # https://studygyaan.com/django/how-to-signup-user-and-send-confirmation-email-in-django
                    # Linguists need permission to be a linguist
                    subject = f"New {group} User"
                    message = f"New user {username} has requested {group} access to {languages}. Login to the admin interface to grant them access."
                    mail_admins(
                        subject,
                        message,
                        fail_silently=True,
                    )
                    group = "Learner"
                group, _ = Group.objects.get_or_create(name=group)
                group.user_set.add(new_user)
                if languages:
                    for language in languages:
                        lang_group, _ = Group.objects.get_or_create(name=language)
                        lang_group.user_set.add(new_user)
                response = HttpResponseRedirect("/login")
                return response

    context = dict(form=form, roles=UserRoles())
    return render(request, "validation/register.html", context)


def view_issues(request, language):
    language = get_language_object(language)
    issues = (
        Issue.objects.filter(status=Issue.OPEN).filter(language=language).order_by("id")
    )

    paginator = Paginator(issues, 10)
    page_no = request.GET.get("page", 1)
    paged_issues = paginator.get_page(page_no)

    context = dict(
        issues=paged_issues,
        auth=request.user.is_authenticated,
        roles=UserRoles(request.user, language.code),
        language=language,
        encode_query_with_page=encode_query_with_page,
    )
    return render(request, "validation/view_issues.html", context)


def view_issue_detail(request, language, issue_id):
    language = get_language_object(language)
    issue = Issue.objects.get(id=issue_id, language=language)

    form = None
    autocomplete = None
    if issue.recording:
        if request.method == "POST":
            form = EditIssueWithRecording(request.POST)
            if request.method == "POST" and form.is_valid():
                form.issue_origin_url = request.session.get(
                    "issue_origin_url", url("validation:issues", language.code)
                )
                return handle_save_issue_with_recording(form, issue, request, language)
        else:
            phrase = issue.source_language_suggestion
            if not phrase:
                phrase = issue.recording.phrase.transcription
            speaker = issue.speaker_suggestion
            if not speaker:
                speaker = issue.recording.speaker
            form = EditIssueWithRecording(
                initial={"phrase": phrase, "speaker": speaker}
            )
            autocomplete = list(
                Phrase.objects.values_list("transcription", flat=True).distinct()
            )

            # Save previous URL to make the "back" button work properly
            request.session["issue_origin_url"] = request.META.get(
                "HTTP_REFERER", url("validation:issues", language.code)
            )
            other_issues = issue.recording.issue_set.filter(~Q(id=issue.id))

    if issue.phrase:
        if request.method == "POST":
            form = EditIssueWithPhrase(request.POST)
            if request.method == "POST" and form.is_valid():
                form.issue_origin_url = request.session.get(
                    "issue_origin_url", url("validation:issues", language.code)
                )
                return handle_save_issue_with_phrase(form, issue, request, language)
        else:
            transcription_initial = issue.source_language_suggestion
            if not transcription_initial:
                transcription_initial = issue.phrase.transcription
            translation_initial = issue.target_language_suggestion
            if not translation_initial:
                translation_initial = issue.phrase.translation

            form = EditIssueWithPhrase(
                initial={
                    "transcription": transcription_initial,
                    "translation": translation_initial,
                }
            )

            # Save previous URL to make the "back" button work properly
            request.session["issue_origin_url"] = request.META.get(
                "HTTP_REFERER", url("validation:issues", language.code)
            )
            other_issues = issue.phrase.issue_set.filter(~Q(id=issue.id))

    context = dict(
        issue=issue,
        form=form,
        auth=request.user.is_authenticated,
        roles=UserRoles(request.user, language.code),
        language=language,
        autocomplete=autocomplete,
        other_issues=other_issues.filter(status="open"),
    )
    return render(request, "validation/view_issue_detail.html", context)


def close_issue(request, language, issue_id):
    language = get_language_object(language)
    issue = Issue.objects.get(id=issue_id, language=language)
    issue.status = Issue.RESOLVED
    issue.save()

    return HttpResponseRedirect(
        request.META.get("HTTP_REFERER", url("validation:issues", language.code))
    )


AVAILABLE_IMAGES = [
    "AnnetteLee",
    "ArleneMakinaw",
    "BettySimon",
    "BrianLightning",
    "DeboraYoung",
    "HarleySimon",
    "IvyRaine",
    "JerryRoasting",
    "KisikawKiseyiniw",
    "LindaOldpan",
    "LouiseWildcat",
    "MaryJeanLittlechild",
    "NormaLindaSaddleback",
    "PaulaMackinaw",
    "RoseMakinaw",
    "RosieRoan",
    "BruceStarlight",
    "JeanOkimāsis",
    "DoloresGreyeyesSand",
    "BrianLee",
    "RonaldLittlechild",
    "MarvinLittlechild",
    "LindaWhitebear",
    "LawrenceWildcat",
    "JackMackinaw",
]


def speaker_view(request, language, speaker_code):
    language = get_language_object(language)
    speaker = language.speaker_set.get(code=speaker_code)
    if speaker:
        full_name = speaker.full_name
    else:
        full_name = f"No speaker found for speaker code {speaker_code}"

    img_name = full_name.title()
    img_name = img_name.replace(" ", "")
    if full_name == "Kîsikâw Kiseyiniw":
        img_name = "KisikawKiseyiniw"
    img_path = f"/static/images/speakers/{img_name}.jpg"
    if img_name not in AVAILABLE_IMAGES:
        img_path = "/static/images/missing.jpg"

    context = dict(
        full_name=full_name,
        auth=request.user.is_authenticated,
        img_path=img_path,
        speaker=speaker,
        language=language,
        roles=UserRoles(request.user, language.code),
    )
    return render(request, "validation/speaker_view.html", context)


def all_speakers(request, language):
    speakers = []
    language = get_language_object(language)
    speaker_objects = language.speaker_set.all()
    for speaker in speaker_objects:
        if (
            "E-" in speaker.code
            or "ELICIT" in speaker.code
            or "/" in speaker.code
            or not speaker.code
        ):
            continue

        full_name = speaker.full_name
        img_name = full_name.title()
        img_name = img_name.replace(" ", "")
        if full_name == "kîsikâw":
            img_name = "Kisikaw"
        img_path = f"/static/images/speakers/{img_name}.jpg"
        if img_name not in AVAILABLE_IMAGES:
            img_path = "/static/images/missing.jpg"

        speaker_dict = dict(
            full_name=full_name,
            code=speaker.code,
            img_path=img_path,
            bio=speaker.target_bio_text or "",
            image_enabled=speaker.image_enabled,
            speaker=speaker,
        )
        speakers.append(speaker_dict)

    context = dict(
        speakers=speakers,
        auth=request.user.is_authenticated,
        language=language,
        roles=UserRoles(request.user, language.code),
    )
    return render(request, "validation/all_speakers.html", context)


# Internal API endpoints


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
        phrase.status = "needs review"
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

    if judgement["judgement"] in ["good", "ok", "bad"]:
        rec.quality = judgement["judgement"]
    else:
        return HttpResponseBadRequest()

    rec.save()
    return JsonResponse({"status": "ok"})


@login_required()
@require_http_methods(["POST"])
def save_wrong_speaker_code(request, language, recording_id):
    language = get_language_object(language)
    rec = get_object_or_404(Recording, id=recording_id)
    speaker = request.POST.get("speaker-code-select")
    referrer = request.POST.get("referrer")

    comment = "This recording has the wrong speaker code."

    if speaker != "idk":
        comment += " The speaker should be: " + speaker

    new_issue = Issue(
        recording=rec,
        comment=comment,
        created_by=request.user,
        speaker_suggestion=(
            Speaker.objects.get(code=speaker) if speaker != "idk" else None
        ),
        created_on=datetime.datetime.now(),
        language=language,
        status=Issue.OPEN,
    )
    new_issue.save()

    rec.wrong_speaker = True

    rec.save()
    if referrer:
        response = HttpResponse(status=HTTPStatus.SEE_OTHER)
        response["Location"] = referrer + "#phrase-" + str(rec.phrase_id)
    else:
        response = HttpResponse(status=HTTPStatus.SEE_OTHER)
        response["Location"] = "/"

    return response


@login_required()
@require_http_methods(["POST"])
def save_wrong_word(request, language, recording_id):
    language = get_language_object(language)
    rec = get_object_or_404(Recording, id=recording_id)
    suggestion = request.POST.get("wrong_word")
    referrer = request.POST.get("referrer")

    comment = "This is the wrong word."

    if suggestion:
        comment += " The word is actually: " + suggestion

    new_issue = Issue(
        recording=rec,
        source_language_suggestion=suggestion,
        comment=comment,
        created_by=request.user,
        created_on=datetime.datetime.now(),
        language=language,
        status=Issue.OPEN,
    )
    new_issue.save()

    rec.wrong_word = True

    rec.save()

    if referrer:
        response = HttpResponse(status=HTTPStatus.SEE_OTHER)
        response["Location"] = referrer + "#phrase-" + str(rec.phrase_id)
    else:
        response = HttpResponse(status=HTTPStatus.SEE_OTHER)
        response["Location"] = "/"

    return response


def record_audio_is_best(request, recording_id):
    phrase_id = json.loads(request.body)["phraseId"]

    recording = get_object_or_404(Recording, id=recording_id)
    if recording.is_best:
        recording.is_best = False
        set_solid = False
    else:
        recording.is_best = True
        set_solid = True
    recording.save()

    # We used to have a single best audio per recording.
    # This is not enforced anymore, to allow multiple best in cases with many entries.
    # This semantic change should be communicated to language experts.

    return JsonResponse({"status": "ok", "set_solid": set_solid})


def approve_user_phrase(request, phrase_id):
    phrase = get_object_or_404(Phrase, id=phrase_id)
    phrase.status = Phrase.NEW
    phrase.save()

    recordings = Recording.objects.filter(phrase_id=phrase.id)
    for rec in recordings:
        rec.is_user_submitted = False
        rec.was_user_submitted = True
        rec.save()

    return JsonResponse({"status": "ok"})


@login_required()
def merge_phrases_view(request, language):
    roles = UserRoles(request.user, language)
    if request.method == "GET" and (roles.is_manager):
        return merge_phrases_search(request, language)
    raise PermissionDenied


def merge_phrases_search(request, language):
    language = get_language_object(language)
    roles = UserRoles(request.user, language.code)

    # Perform search
    candidates = False
    query = request.GET.get("merge-search", "")
    if query:
        candidates = (
            Phrase.objects.filter(language=language)
            .filter(
                Q(transcription__contains=query)
                | Q(fuzzy_transcription__contains=to_indexable_form(query))
                | Q(translation__contains=query)
            )
            .order_by("transcription")
        )

    context = dict(
        # form=form,
        auth=request.user.is_authenticated,
        roles=UserRoles(request.user, language.code),
        language=language,
        candidates=candidates,
    )
    return render(request, f"validation/merge_phrases_search.html", context)


def phrases_can_auto_merge(candidates):
    if candidates.count() < 2:
        return False
    first = candidates[0]
    # Check that each Phrase in the query set is the same:
    for candidate in candidates[1:]:
        if not all(
            [
                candidate.transcription == first.transcription,
                candidate.translation == first.translation,
                candidate.language == first.language,
                candidate.analysis == first.analysis
                or (not candidate.analysis)
                or (not first.analysis),
                candidate.comment == first.comment
                or (not candidate.comment)
                or (not first.comment),
            ]
        ):
            return False
    return True


@login_required()
def merge_phrases_delete(request, language):
    language = get_language_object(language)
    roles = UserRoles(request.user, language.code)
    if not (roles.is_manager):
        raise PermissionDenied
    if request.method == "GET":
        merge_items = [int(id) for id in request.GET.getlist("merge-selected")]
        candidates = Phrase.objects.filter(id__in=merge_items).order_by("transcription")
        if phrases_can_auto_merge(candidates):
            handle_merge_phrases(
                candidates.first(), Phrase.objects.filter(id__in=merge_items[1:]), True
            )
            return HttpResponseRedirect(url("validation:merge-search", language.code))
        context = dict(
            auth=request.user.is_authenticated,
            roles=UserRoles(request.user, language.code),
            language=language,
            candidates=candidates,
        )
        return render(request, f"validation/merge_phrases_candidate.html", context)
    if request.method == "POST":
        destination = request.POST.get("merge-canonical", "")
        if destination:
            # The idea of the last check is that we should do nothing unless explicitly told where to place merge destinations.
            merge_items = [
                int(id)
                for id in request.POST.getlist("merge-selected")
                if id != destination
            ]
            should_deep_merge = destination == "MERGE"
            if len(merge_items) > 0:
                if should_deep_merge:
                    destination = merge_items[0]
                    merge_items = merge_items[1:]
                candidates = Phrase.objects.filter(id__in=merge_items)
                handle_merge_phrases(
                    Phrase.objects.get(id=int(destination)),
                    candidates,
                    should_deep_merge,
                )
        return HttpResponseRedirect(url("validation:merge-search", language.code))
    raise PermissionDenied


@login_required()
def record_audio(request, language):
    language = get_language_object(language)
    transcription = request.GET.get("transcription") or ""
    translation = request.GET.get("translation") or ""

    if request.method == "POST":
        form = RecordNewPhrase(request.POST, request.FILES)
        translation = request.POST.get("translation")
        translation = clean_text(translation)
        transcription = request.POST.get("transcription")
        transcription = clean_text(transcription)
        audio_data = request.FILES["audio_data"]

        # To allow for homonym differentiation, we check that the translation is *exactly* the same
        # There's likely a better way of doing this, but this should suffice for now
        phrase = Phrase.objects.filter(
            transcription=transcription, translation=translation, language=language
        ).first()
        if not phrase:
            phrase = Phrase(
                translation=translation,
                field_transcription=transcription,
                transcription=transcription,
                kind=Phrase.SENTENCE if " " in transcription else Phrase.WORD,
                status=Phrase.USER,
                date=datetime.datetime.now(),
                modifier=request.user,
                language=language,
            )
            phrase.save()

        speaker = Speaker.objects.filter(user=request.user).first()
        if not speaker:
            speaker = Speaker(
                full_name=request.user.first_name + " " + request.user.last_name,
                code=request.user.username,
                user=request.user,
            )
            speaker.save()

        if language not in speaker.languages.all():
            # Can only add language after the object exists i.e. is saved
            speaker.languages.add(language)
            speaker.save()

        recording_session, created = RecordingSession.get_or_create_by_session_id(
            SessionID(
                date=datetime.date.today(),
                time_of_day=None,
                subsession=None,
                location=None,
            )
        )

        rec_id = create_new_rec_id(phrase, speaker)
        audio_data.name = rec_id + ".wav"
        rec = Recording(
            id=rec_id,
            compressed_audio=audio_data,
            speaker=speaker,
            phrase=phrase,
            timestamp=0,
            comment=f"Uploaded by user: {request.user}",
            is_user_submitted=True,
            session_id=recording_session.id,
        )
        rec.save()
        source = settings.RECVAL_AUDIO_PREFIX + rec_id + ".wav"
        dest = settings.RECVAL_AUDIO_PREFIX + rec_id + ".m4a"
        audio_info = mutagen.File(settings.MEDIA_ROOT + "/" + source).info
        new_length = (
            audio_info.length - 0.1
        )  # It takes the average human 0.1 seconds to click down on a button
        subprocess.check_call(
            ["ffmpeg", "-i", source, "-ss", "0", "-to", str(new_length), dest],
            cwd=settings.MEDIA_ROOT,
        )
        rec.compressed_audio = dest
        rec.save()

        save_metadata_to_file(
            rec_id, request.user, transcription, translation, language.name
        )

        context = dict(
            form=form,
            auth=request.user.is_authenticated,
            roles=UserRoles(request.user, language.code),
            language=language,
        )
        return HttpResponseRedirect(f"/{language.code}/record_audio", context)
    else:
        form = RecordNewPhrase(
            {"transcription": transcription, "translation": translation}
        )
        form.fields["transcription"].label = language.endonym

    context = dict(
        form=form,
        auth=request.user.is_authenticated,
        roles=UserRoles(request.user, language.code),
        language=language,
    )
    return render(request, f"validation/record_audio.html", context)


@login_required()
def record_audio_from_entry(request, language, phrase):
    language = get_language_object(language)
    transcription = request.GET.get("transcription")
    translation = request.GET.get("translation")
    # phrase = request.GET.get("phrase")
    print(phrase)

    phrase_object = Phrase.objects.get(id=phrase)

    # form = RecordNewPhrase(request.POST, request.FILES)
    # translation = request.POST.get("translation")
    # translation = clean_text(translation)
    # transcription = request.POST.get("transcription")
    # transcription = clean_text(transcription)
    audio_data = request.FILES["audio_data"]

    speaker = Speaker.objects.filter(user=request.user).first()
    if not speaker:
        speaker = Speaker(
            full_name=request.user.first_name + " " + request.user.last_name,
            code=request.user.username,
            user=request.user,
        )
        speaker.save()

    if language not in speaker.languages.all():
        # Can only add language after the object exists i.e. is saved
        speaker.languages.add(language)
        speaker.save()

    recording_session, created = RecordingSession.get_or_create_by_session_id(
        SessionID(
            date=datetime.date.today(),
            time_of_day=None,
            subsession=None,
            location=None,
        )
    )

    rec_id = create_new_rec_id(phrase_object, speaker)
    audio_data.name = rec_id + ".wav"
    rec = Recording(
        id=rec_id,
        compressed_audio=audio_data,
        speaker=speaker,
        phrase=phrase_object,
        timestamp=0,
        comment=f"Uploaded by user: {request.user}",
        is_user_submitted=True,
        session_id=recording_session.id,
    )
    rec.save()
    source = settings.RECVAL_AUDIO_PREFIX + rec_id + ".wav"
    dest = settings.RECVAL_AUDIO_PREFIX + rec_id + ".m4a"
    audio_info = mutagen.File(settings.MEDIA_ROOT + "/" + source).info
    new_length = (
        audio_info.length - 0.1
    )  # It takes the average human 0.1 seconds to click down on a button
    subprocess.check_call(
        ["ffmpeg", "-i", source, "-ss", "0", "-to", str(new_length), dest],
        cwd=settings.MEDIA_ROOT,
    )
    rec.compressed_audio = dest
    rec.save()

    save_metadata_to_file(
        rec_id, request.user, transcription, translation, language.name
    )

    response = {"status": "ok"}
    json_response = JsonResponse(response)
    return add_cors_headers(json_response)


def set_language(request, language_code):
    assert get_object_or_404(LanguageVariant, code=language_code)

    response = HttpResponse(status=HTTPStatus.SEE_OTHER)
    response["Location"] = reverse(
        "validation:entries", kwargs={"language": language_code}
    )

    return response


@staff_member_required
def throw_500(request):
    raise Exception("test error")


# Small Helper functions


def merge_strings(join_str=" | "):
    def merge_function(destination, field, string_set):
        values = [(" ".join(s.split()).strip()) for s in string_set if s]
        setattr(destination, field, join_str.join(values))

    return merge_function


def merge_many_to_many(destination, field, dataset):
    manager = getattr(destination, field)
    for entries in dataset:
        for entry in entries.all():
            manager.add(entry)


def merge_int_with_function(function):
    def merge_function(destination, field, set):
        setattr(destination, field, function(set))

    return merge_function


def different_contents_queryset(field, dest_value):
    if hasattr(dest_value, "all"):
        # The field is likely a many to many field, or some other using a RelatedManager
        return ~Q(**{(field + "__in"): dest_value.all()})
    return ~Q(**{field: dest_value})


def handle_merge_phrases(destination, sources, should_deep_merge):

    # Change all the phrases on the recordings for sources to the new canonical phrase
    for source in sources:
        for recording in source.recording_set.all():
            recording.phrase = destination
            recording.save(update_fields=["phrase"])

    # Check for all fields in the set:
    if should_deep_merge:
        fields = {
            "field_transcription": merge_strings(),
            "transcription": merge_strings(),
            "translation": merge_strings(),
            "stem": merge_strings(),
            "lexical_category": merge_strings(),
            "osid": merge_strings(),
            "analysis": merge_strings("\n"),
            "comment": merge_strings(),
            "display_order": merge_int_with_function(min),
            "semantic_class": merge_many_to_many,
        }
        updated = []
        for field, merge_fields in fields.items():
            dest_value = getattr(destination, field)
            if (
                sources.filter(different_contents_queryset(field, dest_value)).count()
                > 0
            ):
                # There is a different field!  Thus we must merge.
                values = {getattr(entry, field) for entry in sources}
                values.add(dest_value)
                merge_fields(destination, field, values)
                updated.append(field)
        destination.save()

    # Delete each of the source phrases
    sources.delete()


def handle_save_issue_with_recording(form, issue, request, language):
    rec = Recording.objects.get(id=issue.recording.id)

    speaker_code = form.cleaned_data["speaker"]
    if speaker_code and (not rec.speaker or rec.speaker.code != speaker_code):
        speaker = Speaker.objects.get(code=speaker_code)
        rec.speaker = speaker

    new_word = form.cleaned_data["phrase"].strip()
    if new_word and (not rec.phrase or rec.phrase.transcription != new_word):
        new_phrase = Phrase.objects.filter(transcription=new_word).first()
        if not new_phrase:
            new_phrase = Phrase(
                field_transcription=new_word,
                transcription=new_word,
                translation="",
                kind="Sentence" if " " in new_word else "Word",
                date=datetime.datetime.now(),
                modifier=str(request.user),
            )
            new_phrase.save()
        rec.phrase_id = new_phrase.id

    rec.wrong_word = False
    rec.wrong_speaker = False
    rec.save()

    issue.status = Issue.RESOLVED
    issue.save()
    return HttpResponseRedirect(
        form.issue_origin_url
        if form.issue_origin_url
        else url("validation:issues", language.code)
    )


def handle_save_issue_with_phrase(form, issue, request, language):
    phrase = Phrase.objects.get(id=issue.phrase.id)

    transcription = form.cleaned_data["transcription"].strip()
    translation = form.cleaned_data["translation"].strip()

    if transcription:
        phrase.transcription = transcription
        if " " in transcription:
            phrase.kind = Phrase.SENTENCE
        else:
            phrase.kind = Phrase.WORD
    if translation:
        phrase.translation = translation

    phrase.status = "linked"
    phrase.modifier = str(request.user)
    phrase.date = datetime.datetime.now()
    phrase.save()

    issue.status = Issue.RESOLVED
    issue.save()
    return HttpResponseRedirect(
        form.issue_origin_url
        if form.issue_origin_url
        else url("validation:issues", language.code)
    )


def encode_query_with_page(query, page):
    if not query:
        query = QueryDict("", mutable=True)
    query["page"] = page
    return f"?{query.urlencode()}"


@login_required()
def statistics_page(request, language):
    """
    The language statistics page
    """
    language_object = get_language_object(language)

    context = dict(
        language=language_object,
        roles=UserRoles(request.user, language),
        statistics=collect_statistics(language_object),
    )
    return render(request, "validation/statistics.html", context)


def collect_statistics(language):
    phrases = language.phrase_set.all()
    historical = (
        HistoricalPhrase.objects.filter(Q(id__in=phrases) & ~Q(history_user=None))
        .values("id")
        .distinct()
    )
    transcriptions = {x["transcription"] for x in phrases.values("transcription")}
    split = [x.split(" ") for x in transcriptions]
    lengths = Counter([len(x) for x in split])
    words = {word for sentence in split for word in sentence}
    stats = {
        "Number of entries (words/phrases)": phrases.count(),
        "Number of distinct transcriptions": len(transcriptions),
        "Total distinct words (including as part of sentences)": len(words),
        "Number of entries touched by a human in speech-db": historical.count(),
        "Number of entries with an empty linguistic analysis": phrases.filter(
            analysis=""
        ).count(),
        "Number of entries with a green heading": phrases.filter(
            validated=True
        ).count(),
        "Number of entries with a red heading": phrases.filter(
            ~Q(validated=True) & Q(status=Phrase.REVIEW)
        ).count(),
        "Number of entries with a grey heading": phrases.filter(
            ~Q(validated=True) & ~Q(status=Phrase.REVIEW)
        ).count(),
        "Number of entries with an origin different than new word": phrases.filter(
            ~Q(origin=Phrase.NEW_WORD)
        ).count(),
        "Number of entries manually marked good": phrases.filter(
            origin=Phrase.NEW_WORD, status=Phrase.LINKED
        ).count(),
        "Number of entries manually marked needs review": phrases.filter(
            origin=Phrase.NEW_WORD, status=Phrase.REVIEW
        ).count(),  # TODO Separate No/IDK
        "Number of entries where the 'I don't know' button appears marked": phrases.filter(
            Q(origin=Phrase.NEW_WORD) & ~Q(status="linked") & ~Q(status="needs review")
        ).count(),
    }
    for key, value in lengths.most_common():
        ending = "s" if int(key) > 1 else ""
        stats[f"Number of transcriptions with {key} word{ending}"] = value

    recordings = Recording.objects.filter(phrase__in=phrases)
    unissued_recordings = recordings.filter(
        wrong_word=False, wrong_speaker=False, is_user_submitted=False
    )
    stats["Total recordings"] = recordings.count()
    stats["Total recordings without declared issues"] = unissued_recordings.count()
    stats["Total recordings marked good quality"] = unissued_recordings.filter(
        quality=Recording.GOOD
    ).count()
    stats["Total recordings marked bad quality"] = recordings.filter(
        quality=Recording.BAD
    ).count()
    stats["Total recordings marked unknown quality"] = unissued_recordings.filter(
        quality=Recording.UNKNOWN
    ).count()
    stats["Total recordings marked best"] = recordings.filter(is_best=True).count()

    historical = HistoricalRecording.objects.filter(
        Q(id__in=recordings) & ~Q(history_user=None)
    ).values("id")
    counted = phrases.annotate(
        total_recordings=Count("recording", distinct=True),
        human_touched_recordings=Count(
            Case(When(recording__in=historical, then=1), output_field=IntegerField())
        ),
    )
    stats["Total recordings touched by a human"] = Recording.objects.filter(
        id__in=historical
    ).count()
    stats[
        "Total phrases where all recordings have been touched by a human in speech-db"
    ] = counted.filter(total_recordings=F("human_touched_recordings")).count()
    stats[
        "Total phrases where some recordings have been touched by a human in speech-db"
    ] = counted.filter(human_touched_recordings__gt=0).count()
    stats[
        "Total phrases where no recordings have been touched by a human in speech-db"
    ] = counted.filter(human_touched_recordings=0).count()
    return stats


def user_has_alexis_permissions(user):
    return user.groups.filter(name="stoney-alexis").exists()


def prep_phrase_data(request, phrases, lang):
    # The _segment_card needs a dictionary of recordings
    # in order to properly display search results
    recordings = {}
    forms = {}
    for phrase in phrases:
        recordings[phrase] = [rec for rec in phrase.recordings if rec.speaker != "DAR"]

        if request.method == "POST" and int(request.POST.get("phrase_id")) == phrase.id:
            forms[phrase.id] = FlagSegment(
                request.POST, initial={"phrase_id": phrase.id}
            )
        else:
            forms[phrase.id] = FlagSegment(initial={"phrase_id": phrase.id})
            forms[phrase.id].fields[
                "source_language_suggestion"
            ].label = f"{lang} suggestion"

    return recordings, forms


def save_issue(data, user):
    phrase_id = data["phrase_id"]
    comment = data["comment"]
    source_language_suggestion = data["source_language_suggestion"]
    target_language_suggestion = data["target_language_suggestion"]

    phrase = Phrase.objects.get(id=phrase_id)
    phrase.validated = False
    phrase.status = "needs review"
    phrase.save()

    new_issue = Issue(
        phrase=phrase,
        comment=comment,
        source_language_suggestion=source_language_suggestion,
        target_language_suggestion=target_language_suggestion,
        created_by=user,
        created_on=datetime.datetime.now(),
        status=Issue.OPEN,
    )

    new_issue.save()


def exclude_known_bad_recordings(recordings: QuerySet):
    """
    Given a QuerySet of Recording objects, remove recordings that should NOT be
    presented to users of e.g., the dictionary.
    """
    return (
        recordings.exclude(quality=Recording.BAD)
        .exclude(wrong_word=True)
        .exclude(wrong_speaker=True)
        .exclude(is_user_submitted=True)
        # We use the "gender" field as a proxy to see whether a speaker's data has
        # been properly filled out: exclude speakers whose gender field has not been
        # input. An admin must put *something* in the gender field before the
        # speaker shows up in API results.
        .exclude(speaker__gender__isnull=True)
    )


def create_new_rec_id(phrase, speaker):
    # Generate a unique ID for all user-submitted recordings
    # Since these don't have a timestamp or a session,
    # we use time.time() to add a truly unique element
    # to each signature
    signature = (
        f"speaker: {speaker}\n"
        f"timestamp: 0\n"
        f"{phrase.kind}: {phrase.transcription}\n"
        "\n"
        f"{phrase.translation}\n"
        f"{time.time()}\n"
    )
    return sha256(signature.encode("UTF-8")).hexdigest()


def save_metadata_to_file(rec_id, user, transcription, translation, language):
    dest = (
        settings.MEDIA_ROOT
        + "/"
        + settings.RECVAL_AUDIO_PREFIX
        + "metadata/"
        + rec_id
        + ".json"
    )
    data = {
        "audio_file_name": rec_id + ".wav",
        "user_id": user.id,
        "username": user.username,
        "full_name": user.first_name + " " + user.last_name,
        "recorded_on": str(datetime.datetime.now().astimezone()),
        "transcription": transcription,
        "translation": translation,
        "language": language,
    }
    with open(dest, "w+") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def clean_text(text):
    ret = text.strip()
    ret = ret.replace("\\n", "")
    ret = ret.replace("\\t", "")
    return ret


def get_language_object(language):
    return get_object_or_404(LanguageVariant, code=language)


def replace_circumflexes(term):
    ret_term = (
        term.replace("ê", "ē").replace("â", "ā").replace("î", "ī").replace("ô", "ō")
    )
    return ret_term
