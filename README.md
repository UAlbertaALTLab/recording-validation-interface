Maskwacîs recordings validation
===============================

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
SQLALCHEMY_DATABASE_URI = recval
SECRET_KEY =  # generate a cryptographically generated key for this
SECURITY_PASSWORD_SALT =  # generate a cryptographically generated salt for this
```

Save this file somewhere. If it's the deployed/production version of the
site, save this file outside of the repository, and outside of
`DOCUMENT_ROOT`. For local development, it's fine to have this file in
the local directory.

Finally, create a file called `.env` in the current working
directory, based on the following template:

```sh
# Location of the WSGI app:
export FLASK_APP=recval.app
export RECVAL_SETTINGS=/path/to/recval_settings.py
```

If you're running on a subdirectory (e.g.,
https://sapir.artsrn.ualberta.ca/validation), rather than on
a virtualhost (e.g., https://validation.artsrn.ualberta.ca/), use
the following `.env` instead:

```sh
export FLASK_SCRIPT_NAME=/validation
# Location of the WSGI app, with middleware:
export FLASK_APP=recval.with_script_name_middleware:create_app
export RECVAL_SETTINGS=/path/to/recval_settings.py
```


### Creating the database for the first time

Before you import any data, you need the "Master Recording MetaData"
(sic) spreadsheet, available on Google Drive. Either export this
manually as a CSV file to `./etc/metadata.csv`, or, using the [gdrive][]
command, run the following script to download it automatically:

    flask metadata download

Use `flask db init` to create the initial database. Use it
like this:

    flask init db /path/to/sessions

`/path/to/sessions/` should be a directory filled with directories (or
symbolic links to directories) with filenames in the form of:

    {ISOdate}-{AM/PM}-{Location or '___'}-{Subsession or '0'}

For example, on Sapir, I might have something like this:

    $ ls ~/av/backup-mwe/sessions/
    2015-05-08-AM-___-0
    2016-05-16-PM-___-0
    2016-11-28-AM-US-2
    2017-05-25-AM-DS-2
    2018-04-18-AM-KCH-0
    ...

Each directory should have `*.TextGrid` files paired with a `*.wav` file:

    $ ls -F1 ~/av/backup-mwe/sessions/2015-05-08-AM-___-0/
    2015-05-08-01.TextGrid
    2015-05-08-01.wav
    2015-05-08-02.TextGrid
    2015-05-08-02.wav
    2015-05-08-03.TextGrid
    2015-05-08-03.wav
    ...

So, in order to create the database on Sapir, I type the following:

    flask metadata download
    flask db init /data/av/backup-mwe/sessions


[gdrive]: https://github.com/prasmussen/gdrive


### Creating new users

Once the database is created, you can register new users using the
`flask user create` command:

    $ flask user create --validator user@domain.net
    Creating user with email user@domain.net
    Enter a new password for user@domain.net: ********
    Re-type password: ********
    Creating user:
      Email: herp@derp.net
      Password: ********
      Roles: community, validator
    Is this okay? (y/n) y


Running
-------

Type:

    flask run

This will use the WSGI app configured in `.env`.


Testing
-------

Install the test requirements:

    python3 -m pip install -r test-requirements.txt

Then run:

    ./run-tests

This will type-check the Python code with [mypy], start a temporary
server, and run the tests.

Any additional arguments are passed to `py.test`.

[mypy]: http://mypy-lang.org/


### Rerun tests when the code changes

Ensure you have [entr](http://entrproject.org/) installed. Then:

    ./watch-tests


License
-------

Copyright (C) 2018 Eddie Antonio Santos <easantos@ualberta.ca>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
