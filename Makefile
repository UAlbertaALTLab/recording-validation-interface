# Run common Django commands:
# make install 		-- installs on a production environment
# make install-test -- installs for test environment
# make install-test -- installs for development environment
# make test 		-- run tests

.PHONY: install install-test install-dev install-prod test

install-prod:
	pipenv install
	pipenv run python init --prod --no-debug

install-test: install
	pipenv install --dev
	pipenv run python init --test

install-dev: install
	pipenv install --dev
	pipenv run python init --dev --debug

test:
	mypy librecval
	py.test
