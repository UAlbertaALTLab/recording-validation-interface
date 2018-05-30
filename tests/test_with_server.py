#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from flask import url_for  # type: ignore


def test_index(mock_server):
    """
    The index should redirect to the phrase page.
    """
    r = mock_server.get('/')
    assert r.status_code == 200
    assert 'Maskwacîs Recording' in r.text
