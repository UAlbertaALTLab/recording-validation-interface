#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

import pytest  # type: ignore
from flask import url_for  # type: ignore


@pytest.mark.skip
def test_view_edit_page(app, client, acimosis, validator):
    """
    Trying to change a transcription or translation unvalidated should be an
    error.
    """
    with app.test_request_context():
        route = url_for('edit_phrase', phrase_id=acimosis)
        print(route)
        rv = client.get()
        # Ensure the app does not allow us to do this without logging in.
        assert rv.status_code == 200
