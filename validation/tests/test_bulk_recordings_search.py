"""
Unit/Integration tests for the bulk recordings search API.
"""
import urllib

import pytest  # type: ignore
from django.conf import settings
from django.shortcuts import reverse  # type: ignore

from validation.models import Recording, Phrase, Speaker


@pytest.mark.django_db
def test_search_bulk_recordings(client):
    """
    General test of the recordings search, in the happy case.
    """

    query = "nipiy"
    speaker_code = "MAR"
    phrase = Phrase.objects.filter(transcription=query).first()
    speaker = Speaker.objects.filter(code=speaker_code).first()

    url = reverse("validation:bulk_search_recordings")

    response = client.get(url + "?" + urllib.parse.urlencode([("q", query)]))

    assert "Access-Control-Allow-Origin" in response, "Missing requried CORS headers"

    recordings = response.json()

    assert isinstance(recordings, dict)
    assert len(recordings["matched_recordings"]) == 1
    assert len(recordings["not_found"]) == 0

    recording = recordings["matched_recordings"][0]
    assert recording.get("wordform") == phrase.transcription
    # TODO: Change field name to "speaker_code"?
    assert "speaker" in recording.keys()
    assert recording.get("gender") in ("M", "F")
    assert recording.get("recording_url").startswith(("http://", "https://"))
    assert recording.get("recording_url").endswith(".m4a")
    assert recording.get("speaker_name") == speaker.full_name
    assert recording.get("anonymous") is False
    assert recording.get("speaker_bio_url").startswith(("http://", "https://"))
    assert speaker.code in recording.get("speaker_bio_url")
    assert recording.get("dialect") == speaker.dialect
