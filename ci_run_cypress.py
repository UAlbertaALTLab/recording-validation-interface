from subprocess import check_call, Popen
import os
from pathlib import Path
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--interactive", action="store_true")
args = parser.parse_args()

def modified_env(**kwargs):
    new_env = dict(os.environ)
    new_env.update(kwargs)
    return new_env


TEST_SERVER_PORT = '3001'
TEST_DB = "test_db.sqlite"
TEST_DB_FILE = Path(TEST_DB)

if TEST_DB_FILE.exists():
    TEST_DB_FILE.unlink()

m_env = modified_env(RECVAL_SQLITE_DB_PATH=TEST_DB, USE_DJANGO_DEBUG_TOOLBAR="False")
check_call(["python", "manage.py", "ensuretestdb"], env=m_env)
server = Popen(["python", "manage.py", "runserver", TEST_SERVER_PORT],
               env=m_env)

try:
    cypress_command = "run"
    if args.interactive:
        cypress_command = "open"

    check_call(["node_modules/.bin/cypress", cypress_command],
    env=modified_env(CYPRESS_BASE_URL=f"http://localhost:{TEST_SERVER_PORT}", USE_DJANGO_DEBUG_TOOLBAR="False"))
finally:
    server.terminate()
