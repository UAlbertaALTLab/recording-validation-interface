"""
Empty pytest fixture to prevent the default from doing Too Much

django_db_setup sets up in-memory database by default, but we just want it
to use the test DB, so we override it to do nothing
"""

import pytest


@pytest.fixture(scope="session")
def django_db_setup(django_db_modify_db_settings):
    pass
