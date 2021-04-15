"""
This file is called when running `make integration-test`
It handles the creation of a test database so we know for sure that:
1. There is data we can test against
2. We know what data we're testing against to make the tests simpler
And then it runs Cypress tests against that test DB
"""

import os
import tempfile
from argparse import ArgumentParser
from pathlib import Path
from subprocess import Popen, check_call

parser = ArgumentParser()

# Do you want to run Cypress in interactive mode? Use this flag!
parser.add_argument("--interactive", action="store_true")
args = parser.parse_args()


def modified_env(**kwargs):
    new_env = dict(os.environ)
    new_env.update(kwargs)
    return new_env


TEST_SERVER_PORT = "3001"
TEST_DB = "test_db.sqlite"
TEST_DB_FILE = Path(TEST_DB)

# We delete the DB before we run the tests to make sure there
# aren't any extra users in the DB (i.e. the ones made when
# testing the register process)
if TEST_DB_FILE.exists():
    TEST_DB_FILE.unlink()

# Make a place to dump static files:
with tempfile.TemporaryDirectory(prefix="speech_db_ci_") as temporary_static_directory:
    m_env = modified_env(
        RECVAL_SQLITE_DB_PATH=TEST_DB,
        USE_DJANGO_DEBUG_TOOLBAR="False",
        STATIC_ROOT=temporary_static_directory,
    )
    # Make the test DB!
    check_call(["python", "manage.py", "ensuretestdb"], env=m_env)
    check_call(["python", "manage.py", "collectstatic", "--noinput"], env=m_env)

    # Start up the server
    server = Popen(["python", "manage.py", "runserver", TEST_SERVER_PORT], env=m_env)

    try:
        cypress_command = "run"
        if args.interactive:
            cypress_command = "open"

        # Run Cypress
        check_call(
            ["node_modules/.bin/cypress", cypress_command],
            env=modified_env(
                CYPRESS_BASE_URL=f"http://localhost:{TEST_SERVER_PORT}",
                USE_DJANGO_DEBUG_TOOLBAR="False",
            ),
        )
    finally:
        # Stop the server
        server.terminate()
