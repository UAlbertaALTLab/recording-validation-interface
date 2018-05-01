#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from pathlib import Path


# ################################ General ###################################
REPOSITORY_ROOT = Path(__file__).parent.parent
assert (REPOSITORY_ROOT / '.git').is_dir()

# The default database if none exists.
DEFAULT_DATABASE = 'sqlite:////tmp/recval-temporary.db'


# ################################# Flask ####################################

# TODO: Consider setting APPLICATION_ROOT -- http://flask.pocoo.org/docs/0.12/config/
# TODO: Consider settings USE_X_SENDFILE

# ############################### SQLAlchemy #################################

# Set it to the default database. This SHOULD be overwritten.
SQLALCHEMY_DATABASE_URI = DEFAULT_DATABASE

# Diable object modication tracking -- unneeded, and silences a warning.
# See: http://flask-sqlalchemy.pocoo.org/2.3/config/#configuration-keys
SQLALCHEMY_TRACK_MODIFICATIONS = False


# ################################# RecVal ###################################

TRANSCODED_RECORDINGS_PATH = REPOSITORY_ROOT / 'static' / 'audio'
