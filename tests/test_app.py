#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.


import pytest  # type: ignore
from flask import url_for  # type: ignore

# Start a Flask server for the tests in this module.
pytestmark = pytest.mark.usefixtures("live_server")


def test_index(selenium):
    """
    See if I find a Cree word on the page.
    """
    selenium.get(url_for('list_all_words', _external=True))
    elem = selenium.find_element_by_xpath(
        "//*[contains(text(), 'cakayikan')]"
    )
    # There must be at LEAST one element!
    assert elem.is_displayed()
    assert elem.tag_name == 'td'
