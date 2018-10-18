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

"""
Old CLI commands that should be ported to the new framework.
"""

import shutil
from pathlib import Path

from recval.utils import cd
from recval import REPOSITORY_ROOT

MASTER_RECORDINGS_METADATA = '1SlJRJRUiwXibAxFC0uY2sFXFb4IukGjs7Rg_G1vp_y8'
REMOTE_FILENAME = "Master Recordings MetaData"


def download() -> None:
    """
    Downloads the "Master Recordings MetaData" file from Google Drive, as a
    CSV file.

    This will be downloaded to $REPOSITORY_ROOT/etc/
    """

    from sh import gdrive  # type: ignore
    destination = REPOSITORY_ROOT / 'etc' / 'metadata.csv'
    assert destination.parent.is_dir()

    # Annoyingly, gdrive's "export" command does not allow you to specify an
    # output path, so it will create the file with the **REMOTE FILENAME**.
    # So! Export the file to a temporary directory first, then move it to
    # where we want it to go.
    tmpdir = Path('/tmp/')
    with cd(tmpdir):
        gdrive.export("--force", "--mime", "text/csv",
                      MASTER_RECORDINGS_METADATA,
                      _fg=True)
        exported_csv = (tmpdir / REMOTE_FILENAME).with_suffix('.csv')
        assert exported_csv.exists()
        shutil.copy(exported_csv, destination)
