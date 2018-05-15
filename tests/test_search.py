#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from flask import url_for  # type: ignore


def test_search_box_on_first_page(client):
    """
    The front page should show the search box.
    """
    rv = client.get('/', follow_redirects=True)
    assert 200 == rv.status_code
    assert b'Search' in rv.data


def test_search_box(app, client, acimosis):
    """
    We should be able to search for puppies!
    """

    with app.test_request_context():
        rv = client.get(url_for('search_phrases', q='acîmosis'))
    assert 200 == rv.status_code
    page_html = rv.data.decode('UTF-8')
    assert 'puppy' in page_html
