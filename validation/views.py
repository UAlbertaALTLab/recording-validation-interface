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

from django.conf import settings
from django.urls import reverse
from django.http import FileResponse, HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

from librecval.normalization import normalize_sro

from .models import Phrase, Recording


def index(request):
    """
    The home page.
    """
    all_phrases = Phrase.objects.all()
    paginator = Paginator(all_phrases, 30)
    page_no = request.GET.get('page', 1)
    phrases = paginator.get_page(page_no)
    context = dict(phrases=phrases)
    return render(request, 'validation/list_phrases.html', context)


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
    response = FileResponse(open(settings.RECVAL_AUDIO_DIR / f'{recording.id}.m4a', 'rb'),
                            content_type='audio/m4a')
    # The recording files basically never change, so tell everybody to cache
    # the dookey out these files (or at very least, a year).
    response['Cache-Control'] = f'public, max-age={60 * 60 * 24 * 365}'
    response['ETag'] = f'"{recording.id[:HASH_PREFIX_LENGTH]}"'
    return response


def search_recordings(request, query):
    """
    Searches for recordings whose phrase's transcription matches the query.
    The response is JSON that can be used by external apps (i.e., itwêwina).
    """

    # Maximum amount of comma-separated query terms.
    MAX_RECORDING_QUERY_TERMS = 3

    # Commas are fence posts: there will be one less comma than query terms.
    if query.count(',') >= MAX_RECORDING_QUERY_TERMS:
        response = JsonResponse((), safe=False)
        response.status_code = 414
        response['Access-Control-Allow-Origin'] = '*'
        return response

    word_forms = query.split(',')

    def make_absolute_uri_for_recording(rec_id: str) -> str:
        relative_uri = reverse('validation:recording', kwargs={'recording_id': rec_id})
        return request.build_absolute_uri(relative_uri)

    recordings = []
    for form in word_forms:
        # Assume the query is an SRO transcription
        transcription = normalize_sro(form)

        # HACK: remove the first hyphen in 'ê-' conjuct verbs:
        # I happen to know that the current database content consistently uses
        # ê with no hyphen for conjuct verbs, so we get rid of it here to get
        # more search results.
        # TODO: remove this hack.
        if transcription.startswith('ê-'):
            transcription = transcription.replace('-', '', 1)

        result_set = Recording.objects.filter(phrase__transcription=transcription,
                                              speaker__gender__isnull=False)
        recordings.extend({
            'wordform': rec.phrase.transcription,
            'speaker': rec.speaker.code,
            'gender': rec.speaker.gender,
            'recording_url': make_absolute_uri_for_recording(rec.id),
        } for rec in result_set)

    response = JsonResponse(recordings, safe=False)
    response['Access-Control-Allow-Origin'] = '*'

    if len(recordings) == 0:
        # No matches. Return an empty JSON response
        response.status_code = 404

    return response

# TODO: Speaker bio page like https://ojibwe.lib.umn.edu/about/voices
