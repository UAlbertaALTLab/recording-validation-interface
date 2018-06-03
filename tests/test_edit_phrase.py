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

import pytest  # type: ignore
from flask import url_for  # type: ignore


@pytest.mark.skip
def test_view_edit_page(app, client, acimosis, validator):
    """
    Trying to change a transcription or translation unvalidated should be an
    error.
    """
    with app.test_request_context():
        route = url_for('edit_phrase', phrase_id=acimosis)
        print(route)
        rv = client.get()
        # Ensure the app does not allow us to do this without logging in.
        assert rv.status_code == 200
