import pytest

from librecval.extract_phrases import InvalidFileName, get_mic_id


def test_invalid_mic_id():
    """
    Should raise InvalidFileName when an Track ID cannot be parsed.
    """
    with pytest.raises(InvalidFileName):
        get_mic_id("💩.eaf")
