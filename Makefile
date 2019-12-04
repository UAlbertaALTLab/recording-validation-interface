# Run common Django commands:
# make install 		-- installs on a production environment
# make install-test -- installs for test environment
# make install-dev  -- installs for development environment
# make test 		-- run tests
# make init 		-- initializes the development environment
# make reformat 	-- formats the Python code

.PHONY: init install-test install-dev install-prod test

install-prod:
	pipenv install
	pipenv run python init --prod --no-debug

install-test:
	pipenv install --dev
	pipenv run python init --test

install-dev: init
	pipenv install --dev
	pipenv run python init --dev --debug

test:
	pipenv run mypy librecval
	pipenv run pytest

init:
	git config core.hooksPath .githooks

reformat:
	black librecval tests validation recvalsite
