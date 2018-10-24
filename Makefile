# Run common Django commands:
# make install 		-- installs on a production environment
# make install-test -- installs with test and dev dependencies
# make test 		-- run tests

.PHONY: install install-test test

install:
	pipenv install

install-test: install
	pipenv install --dev
	pipenv run python init

test:
	mypy librecval
	py.test
