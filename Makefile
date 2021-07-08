# Run common Django commands:
# make install 		-- installs on a production environment
# make install-test -- installs for test environment
# make install-dev  -- installs for development environment
# make test 		-- run tests
# make init 		-- initializes the development environment
# make reformat 	-- formats the Python code

.PHONY: init install-test install-dev install-prod migrate test integration-test

install-prod:
	pipenv install --deploy
	pipenv run python init --prod --no-debug

install-test:
	pipenv install --ignore-pipfile --dev
	pipenv run python init --test

install-dev: init
	pipenv install --dev
	pipenv run python init --dev --debug

test:
	pipenv run mypy librecval
	pipenv run pytest

integration-test:
	pipenv run python ci_run_cypress.py

init:
	git config core.hooksPath .githooks

migrate:
	pipenv run python3 manage.py migrate

reformat:
	black librecval tests validation recvalsite

