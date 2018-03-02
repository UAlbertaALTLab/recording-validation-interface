#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.


import pytest

# Use the live server for this test.
pytestmark = pytest.mark.usefixtures("live_server")


def test_index(selenium):
    """
    See if I find a Cree word on the page.
    """
    selenium.get('http://localhost:5000')
    elem = selenium.find_element_by_xpath(
        "//*[contains(text(), 'cakayikan')]"
    )
    # There must be at LEAST one element!
    assert elem.is_displayed()
    assert elem.tag_name == 'td'
