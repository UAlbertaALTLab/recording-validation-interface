#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import warnings

from django.conf import settings
from django.urls import path

from . import views


def media_with_range():
    """
    Return URL patterns that will delegate to serving media from MEDIA_ROOT.
    """

    if not settings.DEBUG:
        return []

    if not settings.MEDIA_URL.startswith("/"):
        warnings.warn(
            f"can only serve media with relative URL; not {settings.MEDIA_URL}"
        )
        return []

    # Remove that starting slash that we required!
    # Django completes with warning (urls.W002) otherwise ¯\_(ツ)_/¯
    media_url = settings.MEDIA_URL[1:]

    # Ensure it has a trailing slash:
    if not media_url.endswith("/"):
        media_url += "/"

    return [path(media_url + "<path:path>", view=views.serve)]
