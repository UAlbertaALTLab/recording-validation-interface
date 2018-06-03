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

from flask import url_for  # type: ignore


def test_search_box_on_first_page(app, client):
    """
    The front page should show the search box.
    """
    rv = client.get('/', follow_redirects=True)
    assert 200 == rv.status_code
    assert b'Search' in rv.data
    with app.test_request_context():
        assert url_for('search_phrases').encode('UTF-8') in rv.data


def test_search_page(app, client, acimosis):
    """
    We should be able to search for puppies!
    """

    with app.test_request_context():
        rv = client.get(url_for('search_phrases', q='acîmosis'))
    assert 200 == rv.status_code
    page_html = rv.data.decode('UTF-8')
    assert 'puppy' in page_html
