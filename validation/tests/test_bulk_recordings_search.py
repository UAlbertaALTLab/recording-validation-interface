"""
Unit/Integration tests for the bulk recordings search API.
"""
import urllib

import pytest  # type: ignore
from django.core.management import call_command
from django.shortcuts import reverse  # type: ignore

from validation.models import Recording, Phrase, Speaker


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "speaker_code"),
    [("nipiy", "MAR"), ("nîpiy", "ROS"), ("awas", "MAR")],
)
def test_search_bulk_recordings(client, query, speaker_code, insert_test_data):
    """
    General test of the recordings search, in the happy case.
    """

    phrase = Phrase.objects.filter(transcription=query).first()
    speaker = Speaker.objects.filter(code=speaker_code).first()

    url = reverse("validation:bulk_search_recordings", args=["maskwacis"])

    response = client.get(url + "?" + urllib.parse.urlencode([("q", query)]))

    assert "Access-Control-Allow-Origin" in response, "Missing required CORS headers"

    recordings = response.json()

    assert isinstance(recordings, dict)
    assert len(recordings["matched_recordings"]) == 1
    assert len(recordings["not_found"]) == 0

    recording = recordings["matched_recordings"][0]
    assert recording.get("wordform") == phrase.transcription
    assert "speaker" in recording.keys()
    assert recording.get("gender") in ("M", "F")
    assert recording.get("recording_url").startswith(("http://", "https://"))
    assert recording.get("recording_url").endswith(".m4a")
    assert recording.get("speaker_name") == speaker.full_name
    assert recording.get("anonymous") is False
    # TODO: make these tests work again?
    # assert recording.get("speaker_bio_url").startswith(("http://", "https://"))
    # assert speaker.code in recording.get("speaker_bio_url")


@pytest.mark.django_db
def test_search_multiple_recordings(client, insert_test_data):
    wordforms = ["nipiy", "nîpiy"]

    url = reverse("validation:bulk_search_recordings", args=["maskwacis"])

    query_params = [("q", form) for form in wordforms]
    response = client.get(url + "?" + urllib.parse.urlencode(query_params))
    recordings = response.json()

    assert isinstance(recordings, dict)
    assert len(recordings["matched_recordings"]) == 2
    assert len(recordings["not_found"]) == 0

    results = recordings["matched_recordings"]
    water_results = [r for r in results if r["wordform"] == "nipiy"]
    assert len(water_results) == 1

    leaf_results = [r for r in results if r["wordform"] == "nîpiy"]
    assert len(leaf_results) == 1

    water_recording = water_results[0]["recording_url"]
    leaf_recording = leaf_results[0]["recording_url"]
    assert water_recording != leaf_recording


@pytest.mark.django_db
def test_search_recordings_not_found(client, insert_test_data):
    real_word = "nîpiy"
    non_word = "Fhqwhgads"
    wordforms = [real_word, non_word]

    url = reverse("validation:bulk_search_recordings", args=["maskwacis"])

    query_params = [("q", form) for form in wordforms]
    response = client.get(url + "?" + urllib.parse.urlencode(query_params))
    recordings = response.json()

    assert isinstance(recordings, dict)
    assert len(recordings["matched_recordings"]) == 1
    assert len(recordings["not_found"]) == 1

    results = recordings["matched_recordings"]
    assert non_word in recordings["not_found"]
    assert all([r["wordform"] == real_word for r in results])


@pytest.mark.django_db
def test_search_language_does_not_exist(client, insert_test_data):
    test_word = "nîpiy"
    wordforms = [test_word]

    url = reverse("validation:bulk_search_recordings", args=["foo-bar"])

    query_params = [("q", form) for form in wordforms]
    response = client.get(url + "?" + urllib.parse.urlencode(query_params))
    recordings = response.json()

    assert isinstance(recordings, dict)
    assert len(recordings["matched_recordings"]) == 0
    assert len(recordings["not_found"]) == 1

    assert test_word in recordings["not_found"]


@pytest.mark.django_db
def test_search_recordings_in_wrong_language(client, insert_test_data):
    test_word = "nîpiy"
    wordforms = [test_word]

    url = reverse("validation:bulk_search_recordings", args=["tsuutina"])

    query_params = [("q", form) for form in wordforms]
    response = client.get(url + "?" + urllib.parse.urlencode(query_params))
    recordings = response.json()

    assert isinstance(recordings, dict)
    assert len(recordings["matched_recordings"]) == 0
    assert len(recordings["not_found"]) == 1

    assert test_word in recordings["not_found"]


@pytest.mark.django_db
def test_search_recordings_with_macrons(client, insert_test_data):
    test_word = "nipâw"
    wordforms = [test_word]
    phrase = Phrase.objects.filter(transcription="nipāw").first()
    speaker = Speaker.objects.filter(code="OKI").first()

    url = reverse("validation:bulk_search_recordings", args=["moswacihk"])

    query_params = [("q", form) for form in wordforms]
    response = client.get(url + "?" + urllib.parse.urlencode(query_params))

    recordings = response.json()

    assert isinstance(recordings, dict)
    assert len(recordings["matched_recordings"]) == 1
    assert len(recordings["not_found"]) == 1

    recording = recordings["matched_recordings"][0]
    assert recording.get("wordform") == phrase.transcription
    assert "speaker" in recording.keys()
    assert recording.get("gender") in ("M", "F")
    assert recording.get("recording_url").startswith(("http://", "https://"))
    assert recording.get("recording_url").endswith(".m4a")
    assert recording.get("speaker_name") == speaker.full_name
    assert recording.get("anonymous") is False


@pytest.fixture
def insert_test_data():
    call_command(
        "loaddata",
        "test_language",
        "speaker_info",
        "test_recordingsession",
        "test_phrases",
        "test_recordings",
    )
