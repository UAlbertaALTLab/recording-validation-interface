#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from unicodedata import normalize

import pytest  # type: ignore
from flask import url_for  # type: ignore


def test_index(selenium, my_live_server):
    """
    See if I find a Cree word on the page.
    """
    url = my_live_server.url(url_for('list_all_words'))
    selenium.get(url)
    elem = selenium.find_element_by_xpath(
        "//*[contains(text(), 'cakayikan')]"
    )
    # There must be at LEAST one element!
    assert elem.is_displayed()
    assert elem.tag_name == 'td'


def test_word_related_to_sentence(selenium, my_live_server):
    """
    Determine whether a Cree word is related to a sentence.
    """
    url = my_live_server.url(url_for('list_all_words'))
    selenium.get(url)
    sentence = normalize('NFC', "êwitikocik êkwa êwitikopêcik")
    elem = selenium.find_element_by_xpath(
        f"//*[contains(text(), '{sentence}')]"
    )
    # There must be at LEAST one element!
    assert elem.is_displayed()

    # TODO: assert that it's associated with a word
