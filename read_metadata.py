#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Parse the metadata file.
"""

import csv
from typing import Any, Dict, Optional, List

from recval.recording_session import SessionID, SessionParseError


def number_from(mic_name: str) -> int:
    """
    Return the mic number.
    """
    assert mic_name.startswith('MIC')
    n = int(mic_name.split()[1])
    assert 1 <= n <= 10
    return n


def normalize_speaker_name(name: str) -> Optional[str]:
    """
    Return the speaker name in a consistence manner.
    If the speaker is N/A or not specified, returns None.
    """
    cleaned = name.strip()
    if cleaned.upper() in ('N/A', ''):
        return None
    return cleaned.upper()


class SessionMetadata:
    def __init__(self, session: SessionID, raw_name: str, mics=Dict[int, str]) -> None:
        self.session = session
        self.raw_name = raw_name
        self.mics = mics

    def __getitem__(self, index: int) -> Optional[str]:
        """
        Return the ONE-INDEXED speaker's name.
        """
        if index not in self.mics.keys():
            raise IndexError(f"Invalid mic number: {index}")
        return self.mics.get(index, None)

    def __repr__(self) -> str:
        return (
            f"{type(self).__qualname__}("
            f"session={self.session!r}, "
            f"raw_name={self.raw_name!r}, "
            f"mics={self.mics!r}"
            ")"
        )

    @classmethod
    def parse(cls, row: Dict[str, Any]) -> 'SessionMetadata':
        # Extract "raw" name
        raw_name = row['SESSION']

        # Parse a session out of it
        session = SessionID.parse_dirty(raw_name)

        # Who are speaking on the mics?
        mic_names = [key for key in row.keys() if key.startswith('MIC')]
        assert len(mic_names) >= 3
        mics = {number_from(mic): normalize_speaker_name(row[mic])
                for mic in sorted(mic_names)}

        # TODO: parse the elicitation sheets
        # TODO: parse the rapidwords sesction(s)

        return cls(session=session, raw_name=raw_name, mics=mics)


if __name__ == '__main__':
    with open('metadata.csv') as metadata_file:
        reader = csv.DictReader(metadata_file)

        sessions: Dict[SessionID, SessionMetadata] = {}
        for row in reader:
            if not row['SESSION']:
                continue
            try:
                s = SessionMetadata.parse(row)
            except SessionParseError:
                print("could not parse: ", row)
            else:
                sessions[s.session] = s
