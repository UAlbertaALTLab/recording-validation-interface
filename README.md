Maskwacîs recordings validation
===============================

[![Build Status](https://travis-ci.org/UAlbertaALTLab/recording-validation-interface.svg?branch=master)](https://travis-ci.org/UAlbertaALTLab/recording-validation-interface)

A Django web app for viewing and validating Cree recordings done in Maskwacîs.


Install
-------

Requires Python 3.7 and [Pipenv][].

Consult `system-requirements.txt` for other system dependencies you may
require (e.g., [`ffmpeg`](https://www.ffmpeg.org/)).

You may also want to install and initialize [gdrive][] before
continuing.

[Pipenv]: https://github.com/pypa/pipenv#installation
[gdrive]: https://github.com/prasmussen/gdrive


### Development environment

To install dependencies and setup for development (e.g., your laptop):

```sh
make install-dev
```


### Production

To install dependencies and setup for production (e.g., on the server):

```sh
make install-prod
```


### Testing

To install dependencies and setup for testing (e.g., on Travis-CI):

```sh
make install-prod
```


### Creating the database for the first time

> **WARNING**: This section may be out of date!

Before you import any data, you need the "Master Recording MetaData"
(sic) spreadsheet, available on Google Drive. Either export this
manually as a CSV file to `./private/metadata.csv`, or, using the [gdrive][]
command, run the following script to download it automatically:

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

> **TODO** WHAT ARE THE IMPORTING COMMANDS?

### Creating a superuser (admin)

To access the admin panel, you'll need at least one admin user. To
create one, run the following command and follow the prompts:

```sh
pipenv run python manage.py createsuperuser
```

For more info, see Django's documentation on [createsuperuser][].

[createsuperuser]: https://docs.djangoproject.com/en/2.1/ref/django-admin/#createsuperuser


Running
-------

To run a development server, use the following.

```sh
pipenv run python manage.py runserver
```

The main site should be available at <http://localhost:8000/>. The admin
interface should be available at <http://localhost:8000/admin>.


Testing
-------

To run the tests, type:

```
make test
```

This will run the [mypy][] static type checker, and then [pytest][].

[mypy]: http://mypy-lang.org/
[pytest]: https://docs.pytest.org/en/latest/

To edit the tests for `librecval`, see `tests/`. For Django tests, look
inside the `validation/tests` directory.


Frequently Asked Questions
--------------------------

### What is “recval”?

It's short for **Rec**ordings **val**idation. I didn't want to type that
out all the time, and I didn't want to puts spaces, hyphens or
underscores to refer to it.

### What is `librecval`?

`librecval` is a library for extracting recordings, transcoding
recordings to a normalized format, and combining the recordings with
metadata, as well as representing recordings data in an
framework-agnostic way. This library *should* be devoid of references or
dependencies on any web framework or database backend.

### What is `recvalsite`?

It's the Django project for the **rec**ording **val**idation **site**.
This aggregates all of the Django apps under one deployable website.


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
