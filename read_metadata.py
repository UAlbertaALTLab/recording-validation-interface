#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Parse the metadata file.
"""

import csv
from typing import Any, Dict, Optional

from recval.recording_session import RecordingSession


def number_from(mic_name: str) -> int:
    """
    Return the mic number.
    """
    assert mic_name.startswith('MIC')
    n = int(mic_name.split()[1])
    assert 1 <= n <= 10
    return n


def normalize_speaker_name(name: str) -> str:
    cleaned = name.strip()
    if cleaned.upper() == 'N/A':
        return None
    return cleaned


class SessionMetadata:
    def __init__(self, raw_name: str, mics=Dict[int, str]) -> None:
        self.raw_name = raw_name
        self.mics = mics

    def __getitem__(self, index: int) -> Optional[str]:
        """
        Return the ONE-INDEXED speaker's name.
        """
        return self.mics.get(index, None)

    def __repr__(self) -> str:
        return (
            f"{type(self).__qualname__}(raw_name={self.raw_name!r}, "
            f"mics={self.mics!r})"
        )

    @classmethod
    def parse(cls, row: Dict[str, Any]) -> 'SessionMetadata':
        # Extract "raw" name

        # Parse a session out of it

        # parse who's on the mics
        mic_names = [key for key in row.keys() if key.startswith('MIC')]
        assert len(mic_names) >= 3
        mics = {number_from(mic): normalize_speaker_name(row[mic])
                for mic in sorted(mic_names)}

        # TODO: parse the elicitation sheets
        # TODO: parse the rapidwords sesction(s)

        return cls(raw_name=row['SESSION'], mics=mics)


if __name__ == '__main__':
    with open('metadata.csv') as metadata_file:
        reader = csv.DictReader(metadata_file)

        sessions = [SessionMetadata.parse(row)
                    for row in reader if row['SESSION']]
