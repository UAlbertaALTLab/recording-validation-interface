# Maskwacîs recordings validation

An app for viewing and validating recordings done in Maskwacîs.


Install
-------

Requires Python 3.6.

Create a virtualenv (if applicable), and install the requirements:

    python3 -m pip install -r requirements.txt

Consult `system-requirements.txt` for other system dependencies you may
require (e.g., [`ffmpeg`](https://www.ffmpeg.org/)).

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

Finally, create a file called `.flaskenv` in the current working
directory, based on the following template:

```sh
# Location of the WSGI app:
export FLASK_APP=recval.app
export RECVAL_SETTINGS=/path/to/recval_settings.py
```

### Creating the database for the first time

Use the `./create_db.py` script (after setting `RECVAL_SETTINGS`; see
below) to create the initial database. Use it like this:

    ./create_db.py /path/to/sessions/

`sessions/` is a directory filled with directories (or symbolic
links to directories) with filenames in the form of:

    {ISOdate}-{AM/PM}-{Location or '___'}-{Subsession or '0'}

For example, on Sapir, I might have something like this:

    $ ls ~/av/backup-mwe/sessions/
    2015-05-08-AM-___-0
    2016-05-16-PM-___-0
    2016-11-28-AM-US-2
    2017-05-25-AM-DS-2
    2018-04-18-AM-KCH-0
    ...

Each directory should have `*.TextGrid` files pair with a `*.wav` file:

    $ ls -F1 ~/av/backup-mwe/sessions/2015-05-08-AM-___-0/
    2015-05-08-01.TextGrid
    2015-05-08-01.wav
    2015-05-08-02.TextGrid
    2015-05-08-02.wav
    2015-05-08-03.TextGrid
    2015-05-08-03.wav
    ...


### Creating new users

Once the database is created, you can register new users using the
`./manage.py` command (after setting `RECVAL_SETTINGS`; see below):

    $ ./manage.py create user@domain.net
    Creating user with email user@domain.net
    Enter a new password for user@domain.net: ********
    Re-type password: ********
    Creating validator:
      Email: herp@derp.net
      Password: ********
    Is this okay? (y/n) y


Running
-------

Type

```
flask run
```

This should use the WSGI app configured in `.flaskenv`.


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
