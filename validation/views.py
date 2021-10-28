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
import subprocess
import time
from hashlib import sha256
from http import HTTPStatus
import datetime
import io
import json
import operator
from functools import reduce
from pathlib import Path

import mutagen as mutagen
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.paginator import Paginator
from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
    QueryDict,
    HttpRequest,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as django_login
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.db.models import Q, QuerySet

from librecval.normalization import to_indexable_form

from .models import Phrase, Recording, Speaker, RecordingSession, Issue
from .forms import (
    EditSegment,
    Login,
    Register,
    FlagSegment,
    EditIssueWithRecording,
    EditIssueWithPhrase,
    RecordNewPhrase,
)
from .helpers import (
    get_distance_with_translations,
    perfect_match,
    exactly_one_analysis,
    normalize_img_name,
)


def index(request):
    """
    The home page.
    """

    is_linguist = user_is_linguist(request.user)
    is_expert = user_is_expert(request.user)

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
        all_phrases = Phrase.objects.exclude(status=Phrase.USER)
    else:
        all_phrases = Phrase.objects.filter(status=mode)

    all_phrases = all_phrases.prefetch_related("recording_set__speaker")

    sessions = RecordingSession.objects.order_by("id").values("id", "date").distinct()
    session = request.GET.get("session")
    if session != "all" and session:
        all_phrases = all_phrases.filter(recording__session__id=session).distinct()

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

    speakers = Speaker.objects.all()

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
        speakers=speakers,
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
    all_matches = (
        Phrase.objects.filter(
            Q(transcription__contains=query)
            | Q(fuzzy_transcription__contains=to_indexable_form(query))
            | Q(translation__contains=query)
        )
        .exclude(status=Phrase.USER)
        .prefetch_related("recording_set__speaker")
    )
    all_matches = list(all_matches)
    all_matches.sort(key=lambda phrase: phrase.transcription)

    query_term = QueryDict("", mutable=True)
    query_term.update({"query": query})

    paginator = Paginator(all_matches, 5)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)

    recordings, forms = prep_phrase_data(request, phrases)

    speakers = Speaker.objects.all()

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
    kind = request.GET.get("kind")
    status = request.GET.get("status")
    speakers = request.GET.getlist("speaker-options")
    quality = request.GET.get("quality")

    if status and status != "all":
        status_choices = {
            "new": Phrase.NEW,
            "linked": Phrase.LINKED,
            "auto-validated": Phrase.AUTO,
            "user-submitted": Phrase.USER,
        }
        status = status_choices[status]

    filter_query = []
    if transcription:
        filter_query.append(
            Q(fuzzy_transcription__contains=to_indexable_form(transcription))
        )
        filter_query.append(Q(transcription__contains=transcription))
    if translation:
        filter_query.append(Q(translation__contains=translation))
    if analysis:
        filter_query.append(Q(analysis__contains=analysis))
    if status and status != "all":
        filter_query.append(Q(status=status))

    if kind and kind != "all":
        filter_kind = Phrase.WORD if kind == "word" else Phrase.SENTENCE
        filter_query.append(Q(kind=filter_kind))

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
            "kind": kind,
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


def bulk_search_recordings(request: HttpRequest):
    """
    API endpoint to retrieve EXACT wordforms and return the URLs and metadata for the recordings.
    Example: /api/bulk_search?q=mistik&q=minahik&q=waskay&q=mîtos&q=mistikow&q=mêstan
    """

    query_terms = request.GET.getlist("q")
    matched_recordings = []
    not_found = []

    for term in query_terms:
        all_matches = Recording.objects.filter(phrase__transcription=term)
        results = exclude_known_bad_recordings(all_matches)

        if results:
            matched_recordings.extend(
                recording.as_json(request) for recording in results
            )
        else:
            not_found.append(term)

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
def segment_content_view(request, segment_id):
    """
    The view for a single segment
    Returns the selected phrase and info provided by the helper functions
    """
    if request.method == "POST":
        form = EditSegment(request.POST)
        og_phrase = Phrase.objects.get(id=segment_id)
        phrase_id = og_phrase.id
        if form.is_valid():
            transcription = form.cleaned_data["cree"].strip() or og_phrase.transcription
            translation = (
                form.cleaned_data["translation"].strip() or og_phrase.translation
            )
            analysis = form.cleaned_data["analysis"].strip() or og_phrase.analysis
            p = Phrase.objects.get(id=phrase_id)
            p.transcription = transcription
            p.translation = translation
            p.analysis = analysis
            p.validated = True
            p.modifier = str(request.user)
            p.date = datetime.datetime.now()
            p.save()

    phrase = Phrase.objects.get(id=segment_id)
    field_transcription = phrase.field_transcription
    suggestions = get_distance_with_translations(field_transcription)

    segment_name = phrase.transcription

    history = phrase.history.all()
    auth = request.user.is_authenticated

    form = EditSegment(
        initial={
            "cree": phrase.transcription,
            "translation": phrase.translation,
            "analysis": phrase.analysis,
        }
    )

    context = dict(
        phrase=phrase,
        segment_name=segment_name,
        suggestions=suggestions,
        form=form,
        history=history,
        auth=auth,
        is_linguist=user_is_linguist(request.user),
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
                )
                new_user.save()
                if group == "Linguist" or group == "Expert":
                    # https://studygyaan.com/django/how-to-signup-user-and-send-confirmation-email-in-django
                    # Linguists need permission to be a linguist
                    subject = f"New {group} User"
                    message = f"New user {username} has requested {group} access. Login to the admin interface to grant them access."
                    mail_admins(
                        subject,
                        message,
                        fail_silently=True,
                    )
                    group = "Learner"
                group, _ = Group.objects.get_or_create(name=group)
                group.user_set.add(new_user)
                response = HttpResponseRedirect("/login")
                return response

    context = dict(form=form)
    return render(request, "validation/register.html", context)


def view_issues(request):
    issues = Issue.objects.filter(status=Issue.OPEN).order_by("id")
    context = dict(
        issues=issues,
        auth=request.user.is_authenticated,
        is_linguist=user_is_linguist(request.user),
    )
    return render(request, "validation/view_issues.html", context)


def view_issue_detail(request, issue_id):
    issue = Issue.objects.get(id=issue_id)

    form = None
    if issue.recording:
        if request.method == "POST":
            form = EditIssueWithRecording(request.POST)
            if request.method == "POST" and form.is_valid():
                return handle_save_issue_with_recording(form, issue, request)
        else:
            form = EditIssueWithRecording(initial={"phrase": issue.suggested_cree})

    if issue.phrase:
        if request.method == "POST":
            form = EditIssueWithPhrase(request.POST)
            if request.method == "POST" and form.is_valid():
                return handle_save_issue_with_phrase(form, issue, request)
        else:
            form = EditIssueWithPhrase(
                initial={
                    "transcription": issue.suggested_cree,
                    "translation": issue.suggested_english,
                }
            )

    context = dict(
        issue=issue,
        form=form,
        auth=request.user.is_authenticated,
        is_linguist=user_is_linguist(request.user),
    )
    return render(request, "validation/view_issue_detail.html", context)


def close_issue(request, issue_id):
    issue = Issue.objects.filter(id=issue_id).first()
    issue.status = Issue.RESOLVED
    issue.save()

    return HttpResponseRedirect("/issues")


def speaker_view(request, speaker_code):
    speaker = Speaker.objects.get(code=speaker_code)
    if speaker:
        full_name = speaker.full_name
    else:
        full_name = f"No speaker found for speaker code {speaker_code}"

    if speaker.image:
        img_src = speaker.image.url
    else:
        img_src = Path(settings.BASE_DIR / settings.BIO_IMG_PREFIX / "missing.jpg")

    context = dict(
        full_name=full_name,
        auth=request.user.is_authenticated,
        img_src=img_src,
        speaker=speaker,
    )
    return render(request, "validation/speaker_view.html", context)


def all_speakers(request):
    speakers = []
    speaker_objects = Speaker.objects.all()
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
        full_path_name = f"{settings.BASE_DIR}{img_path}"
        if not Path(full_path_name).exists():
            img_path = "/static/images/missing.jpg"

        speaker_dict = dict(
            full_name=full_name,
            code=speaker.code,
            img_path=img_path,
            bio=speaker.eng_bio_text or "",
            speaker=speaker,
        )
        speakers.append(speaker_dict)

    context = dict(speakers=speakers, auth=request.user.is_authenticated)
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

    if judgement["judgement"] in ["good", "bad"]:
        rec.quality = judgement["judgement"]
    else:
        return HttpResponseBadRequest()

    rec.save()
    return JsonResponse({"status": "ok"})


@login_required()
@require_http_methods(["POST"])
def save_wrong_speaker_code(request, recording_id):
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
        created_on=datetime.datetime.now(),
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
def save_wrong_word(request, recording_id):
    rec = get_object_or_404(Recording, id=recording_id)
    suggestion = request.POST.get("wrong_word")
    referrer = request.POST.get("referrer")

    comment = "This is the wrong word."

    if suggestion:
        comment += " The word is actually: " + suggestion

    new_issue = Issue(
        recording=rec,
        suggested_cree=suggestion,
        comment=comment,
        created_by=request.user,
        created_on=datetime.datetime.now(),
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


@login_required()
def record_audio(request):
    if request.method == "POST":
        form = RecordNewPhrase(request.POST, request.FILES)
        translation = request.POST.get("translation")
        translation = clean_text(translation)
        transcription = request.POST.get("transcription")
        transcription = clean_text(transcription)
        audio_data = request.FILES["audio_data"]

        phrase = Phrase.objects.filter(transcription=transcription).first()
        if not phrase:
            phrase = Phrase(
                translation=translation,
                field_transcription=transcription,
                transcription=transcription,
                kind=Phrase.SENTENCE if " " in transcription else Phrase.WORD,
                status=Phrase.USER,
                date=datetime.datetime.now(),
                modifier=request.user,
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

        save_metadata_to_file(rec_id, request.user, transcription, translation)

        context = dict(
            form=form,
            auth=request.user.is_authenticated,
            is_linguist=user_is_linguist(request.user),
        )
        return HttpResponseRedirect("/secrets/record_audio", context)
    else:
        form = RecordNewPhrase()

    context = dict(
        form=form,
        auth=request.user.is_authenticated,
        is_linguist=user_is_linguist(request.user),
    )
    return render(request, "validation/record_audio.html", context)


# Small Helper functions


def handle_save_issue_with_recording(form, issue, request):
    rec = Recording.objects.get(id=issue.recording.id)

    speaker_code = form.cleaned_data["speaker"]
    if speaker_code:
        speaker = Speaker.objects.get(code=speaker_code)
        rec.speaker = speaker

    new_word = form.cleaned_data["phrase"].strip()
    if new_word:
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
    return HttpResponseRedirect("/issues")


def handle_save_issue_with_phrase(form, issue, request):
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
    return HttpResponseRedirect("/issues")


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
    comment = data["comment"]
    cree_suggestion = data["cree_suggestion"]
    english_suggestion = data["english_suggestion"]

    phrase = Phrase.objects.get(id=phrase_id)
    phrase.validated = False
    phrase.status = "needs review"
    phrase.save()

    new_issue = Issue(
        phrase=phrase,
        comment=comment,
        suggested_cree=cree_suggestion,
        suggested_english=english_suggestion,
        created_by=user,
        created_on=datetime.datetime.now(),
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


def save_metadata_to_file(rec_id, user, transcription, translation):
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
        "dialect": "Plains Cree",
    }
    with open(dest, "w+") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def clean_text(text):
    ret = text.strip()
    ret = ret.replace("\n", "")
    ret = ret.replace("\t", "")
    return ret
