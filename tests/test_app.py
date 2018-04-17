#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from unicodedata import normalize

import pytest  # type: ignore
from flask import url_for  # type: ignore
from bs4 import BeautifulSoup


def test_index(selenium, live_server):
    """
    See if I find a Cree word on the page.
    """
    url = live_server.url(url_for('list_phrases'))
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
    rv = client.get(url_for('list_phrases'))
    assert rv.status_code == 200
    webpage = rv.data.decode('UTF-8')

    word = nfc("Nanapowapis")
    assert word in webpage

    sentence = nfc("kayas mana ekinanapwapitacik otemwawa ekosi namoya wahyaw ketohteyiwa")
    assert sentence in webpage

    # TODO: assert that it's associated with a word
    soup = BeautifulSoup(webpage, 'lxml')
    tags = soup.find_all(string=word)
    assert len(tags) == 1
    td, = tags
    assert td.name == 'td'


def nfc(text: str) -> str:
    return normalize('NFC', text)
