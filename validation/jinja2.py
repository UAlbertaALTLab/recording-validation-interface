#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Adpated from: https://medium.com/@samuh/using-jinja2-with-django-1-8-onwards-9c58fe1204dc

from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            # Enables use of {{ static(...) }}
            "static": staticfiles_storage.url,
            # Enables use of {{ url(...) }}
            "url": url,
        }
    )

    # Register filters
    env.filters["audio_url"] = audio_url_filter

    return env


def url(name, *args, **kwargs):
    """
    Small wrapper for Django's reverse() filter.
    """
    return reverse(name, args=args, kwargs=kwargs)


def audio_url_filter(rec) -> str:
    """
    Filter that returns a url to the compressed audio file for this particular
    recording.
     Usage (in a template):
         <source src="{{ recording | audio_url }}" type="audio/aac" />
    """
    return rec.compressed_audio.url
