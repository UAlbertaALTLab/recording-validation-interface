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
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

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
    recording = get_object_or_404(Recording, id=recording_id)
    audio = (settings.RECVAL_AUDIO_DIR / f'{recording.id}.m4a').read_bytes()
    return HttpResponse(audio, content_type='audio/m4a')


# TODO: Speaker bio page like https://ojibwe.lib.umn.edu/about/voices
