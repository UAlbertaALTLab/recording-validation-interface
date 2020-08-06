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

from django.conf import settings
from django.core.paginator import Paginator
from django.http import FileResponse, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from librecval.normalization import to_indexable_form

from .crude_views import *
from .models import Phrase, Recording


def index(request):
    """
    The home page.
    """
    all_phrases = Phrase.objects.all()
    paginator = Paginator(all_phrases, 30)
    page_no = request.GET.get("page", 1)
    phrases = paginator.get_page(page_no)
    context = dict(phrases=phrases)
    return render(request, "validation/list_phrases.html", context)


def search_phrases(request):
    """
    The search results for pages.
    """
    return HttpResponse(501)


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
    # How many digits of the hash to include in the ETag.
    # Practically, we do not need to make the entire hash part of the etag;
    # just a part of it. Note: GitHub uses 7 digits.
    HASH_PREFIX_LENGTH = 7
    recording = get_object_or_404(Recording, id=recording_id)
    audio_dir = Recording.get_path_to_audio_directory()

    local_file_path = audio_dir / f"{recording.id}.m4a"

    if "Range" in request.headers:
        value = request.headers["Range"]

        if not value.startswith("bytes="):
            return HttpResponseBadRequest()

        try:
            _bytes, _equal, range_str = value.partition("=")
            lower_str, _hyphen, upper_str = range_str.partition("-")
            lower = int(lower_str)
            if upper_str:
                upper = int(upper_str)
            else:
                upper = None

            if lower < 0:
                raise ValueError
            if upper is not None and upper < lower:
                raise ValueError

        except ValueError:
            return HttpResponseBadRequest()

        file_contents = local_file_path.read_bytes()
        total_content_length = len(file_contents)

        if not upper:
            upper = total_content_length - 1

        partial_file_contents = file_contents[lower : upper + 1]

        response = FileResponse(
            io.BytesIO(partial_file_contents), content_type="audio/m4a",
        )
        response.status_code = 206
        response["Accept-Ranges"] = "bytes"
        response["Content-Range"] = f"bytes {lower}-{upper}/{total_content_length}"
    else:
        response = FileResponse(local_file_path.open("rb"), content_type="audio/m4a",)
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
        relative_uri = rec.compressed_audio.url
        assert relative_uri.startswith("/")
        return request.build_absolute_uri(relative_uri)

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


# TODO: Speaker bio page like https://ojibwe.lib.umn.edu/about/voices
