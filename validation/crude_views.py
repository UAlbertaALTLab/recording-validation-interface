#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from django.shortcuts import get_object_or_404, render

from .models import RecordingSession

__all__ = ["list_all_sessions"]


def list_all_sessions(request):
    """
    Lists literally all of the sessions.
    """

    sessions = RecordingSession.objects.all().order_by("id")
    return render(
        request, "validation/crude/list_sessions.html", dict(sessions=sessions)
    )
