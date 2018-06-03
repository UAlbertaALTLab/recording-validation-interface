#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright (C) 2018 Eddie Antonio Santos <easantos@ualberta.ca>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from pathlib import Path


# ################################ General ###################################
REPOSITORY_ROOT = Path(__file__).parent.parent
assert (REPOSITORY_ROOT / '.git').is_dir()

# The default database if none exists.
DEFAULT_DATABASE = 'sqlite:////tmp/recval-temporary.db'


# ################################# Flask ####################################

# TODO: Consider settings USE_X_SENDFILE:
# See: http://flask.pocoo.org/docs/0.12/config/

# ############################### SQLAlchemy #################################

# Set it to the default database. This SHOULD be overwritten.
SQLALCHEMY_DATABASE_URI = DEFAULT_DATABASE

# Diable object modication tracking -- unneeded, and silences a warning.
# See: http://flask-sqlalchemy.pocoo.org/2.3/config/#configuration-keys
SQLALCHEMY_TRACK_MODIFICATIONS = False


# ############################# Flask-Security ############################# #

# Password hashing algorithm. Either BCrypt or PBKDF2 are good choices.
SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'

# Disable CLIs created by Flask-Security
SECURITY_CLI_USERS_NAME = False
SECURITY_CLI_ROLES_NAME = False


# ################################# RecVal ###################################

TRANSCODED_RECORDINGS_PATH = REPOSITORY_ROOT / 'static' / 'audio'

# NOTE: you must generate a secret key and password salt.  This should be a
# **cryptographically** generated random hash of some sort.  An easy way to
# create one is to use Python3.6's secrets module:
#
# import secrets;
# print(secrets.token_hex())
SECRET_KEY = None
SECURITY_PASSWORD_SALT = None
