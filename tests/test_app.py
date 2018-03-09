#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from unicodedata import normalize

import pytest  # type: ignore
from flask import url_for  # type: ignore


def test_index(selenium, live_server):
    """
    See if I find a Cree word on the page.
    """
    url = live_server.url(url_for('list_all_words'))
    selenium.get(url)
    elem = selenium.find_element_by_xpath(
        "//*[contains(text(), 'cakayikan')]"
    )
    # There must be at LEAST one element!
    assert elem.is_displayed()
    assert elem.tag_name == 'td'


def test_word_related_to_sentence(client):
    """
    Determine whether a Cree word is related to a sentence.
    """
    rv = client.get(url_for('list_all_words'))
    assert rv.status_code == 200

    sentence = normalize('NFC', "êwitikocik êkwa êwitikopêcik")
    assert sentence.encode('UTF-8') in rv.data

    # TODO: assert that it's associated with a word
