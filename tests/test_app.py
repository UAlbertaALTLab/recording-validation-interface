#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


def test_hello_world(selenium):
    """
    Example to figure out if my Selenium config is correct.
    """
    selenium.get('http://localhost:5000')
    h1 = selenium.find_element_by_tag_name('h1')
    assert 'Hello, World' in h1.text
