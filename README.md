# recording-validation-interface

Maskwacîs recordings validation interface.


Install
-------

Requires Python 3.6.

Create a virtualenv (if applicable), and install the requirements:

    python3 -m pip install -r requirements.txt

Consult `system-requirements.txt` for other system dependencies you may require.

Create a file called `recval_settings.py` based on this template:

```python
TRANSCODED_RECORDINGS_PATH = '/path/to/audio/directory'
SQLALCHEMY_DATABASE_URI = 'sqlite:///path/to/recval.db'
SECRET_KEY =  # generate a cryptographically generated key for this
SECURITY_PASSWORD_SALT = # generate a cryptographically generated salt for this
```

Save this file somewhere. If it's the deployed/production version of the
site, save this file outside of the repository, and outside of
`DOCUMENT_ROOT`. For local development, it's fine to have this file in
the local directory.


**TODO**: DOCUMENT HOW TO CREATE THE DATABASE FOR THE FIRST TIME.

Running
-------

When developing and running tests, do this to setup the environment
variables:

    source ./source-this.sh

Otherwise, set the environment variables manually, like so:

    export RECVAL_SETTINGS=/path/to/recval_settings.py

---

Finally, you can run the server!

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
server, and run the tests.

Any additional arguments are passed to `py.test`.


### Rerun tests when the code changes

Ensure you have [entr](http://entrproject.org/) installed. Then:

    ./watch-tests


License
-------

2018 © University of Alberta/Eddie Antonio Santos. All rights reserved.
