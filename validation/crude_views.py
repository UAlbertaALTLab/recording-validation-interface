#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from django.shortcuts import get_object_or_404, render

from .models import RecordingSession

__all__ = ["list_all_sessions", "all_recordings_for_session"]


def list_all_sessions(request):
    """
    Lists literally all of the sessions.
    """

    sessions = RecordingSession.objects.all().order_by("id")
    return render(
        request, "validation/crude/list_sessions.html", dict(sessions=sessions)
    )


def all_recordings_for_session(request, session_id: str):
    session = get_object_or_404(RecordingSession, id=session_id)
    return render(
        request, "validation/crude/list_recordings.html", dict(session=session)
    )
