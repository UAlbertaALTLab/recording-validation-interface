#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
from pathlib import Path

import pytest  # type: ignore


# XXX: gross sys.path manipulation to allow us to
# `import recval` from within the tests
sys.path.append(
    # .parent == ./
    # .parent.parent == ../
    str(Path(__file__).parent.parent.resolve())
)


@pytest.fixture
def app():
    """
    The Flask app. Required by pytest-flask.
    """

    from recval.app import app
    return app
