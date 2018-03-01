#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


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
