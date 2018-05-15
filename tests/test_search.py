#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.


def test_search_on_index(client):
    """
    Going to the front page should show the search box.
    """
    rv = client.get('/', follow_redirects=True)
    assert 200 == rv.status_code
    assert b'Search' in rv.data
