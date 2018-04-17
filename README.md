# recording-validation-interface

Maskwacîs recordings validation interface.


Install
-------

Requires Python 3.6.

Then, create a virtualenv (if applicable), and install the requirements:

    python3 -m pip install -r requirements.txt

Consult `system-requirements.txt` for other system dependencies you may require.

Create a file called `recval.cfg` based on this template:

```python
TRANSCODED_RECORDINGS_PATH = '/path/to/audio/directory'
SQLALCHEMY_DATABASE_URI = '/path/to/recval.db'
```

Save this file somewhere, preferably outside of the repository.


Running
-------

    export RECVAL_SETTINGS=/path/to/recval.cfg
    export FLASK_APP=recval/app.py
    flask run --host HOST

Replace `HOST` with `127.0.0.1` (listen only locally) when running in debug mode.

Replace `HOST` with `0.0.0.0` (listen to all devices) when running in
production mode.


Testing
-------

Install the test requirements:

    python3 -m pip install -r test-requirements.txt

Then run:

    ./run-tests

This will type-check the Python code with mypy, start a temporary
server, and run the Selenium integration tests.

Any additional arguments are passed to `py.test`.


### Rerun tests when the code changes

Ensure you have [entr](http://entrproject.org/) installed. Then:

    ./watch-tests


License
-------

2018 © University of Alberta/Eddie Antonio Santos. All rights reserved.
