#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Temporary dumping ground before I find a better place for whatever is in here.
"""

import os
from contextlib import contextmanager
from pathlib import Path


# Copied from: https://stackoverflow.com/a/24469659/6626414
@contextmanager
def cd(path: Path):
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)
