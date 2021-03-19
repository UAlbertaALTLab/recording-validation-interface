#!/usr/bin/env python3

import pytest

from librecval.extract_phrases import InvalidFileName, get_mic_id


def test_invalid_mic_id():
    with pytest.raises(InvalidFileName):
        get_mic_id("💩.eaf")
