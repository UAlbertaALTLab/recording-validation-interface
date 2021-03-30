from subprocess import check_call, Popen
import os

TEST_SERVER_PORT = '3001'
server = Popen(["python", "manage.py", "runserver", TEST_SERVER_PORT])

try:
    cmd_env = dict(os.environ)
    cmd_env['CYPRESS_BASE_URL'] = f"http://localhost:{TEST_SERVER_PORT}"
    check_call(["node_modules/.bin/cypress", "run"], env=cmd_env)
finally:
    server.terminate()