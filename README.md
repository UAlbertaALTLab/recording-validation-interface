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

To install dependencies and setup for development (e.g., on your laptop):

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
make install-test
```


### Configuring environment variables

The app needs to know:

 - where the raw recording sessions are
 - where to find the "Recordings Master MetaData" CSV file
 - where to place transcoded audio files

This is configured by creating a file called `.env` in the root of this
repository following this template:

```sh
RECVAL_SESSIONS_DIR=/absolute/path/to/recording/sessions/
RECVAL_METADATA_PATH=/absolute/path/to/master-recordings-metadata.csv
RECVAL_AUDIO_DIR=/absolute/path/to/transcoded/audio/directory/
```

Replace the paths as appropriate.


#### `RECVAL_SESSIONS_DIR`

This directory contains all of the recording sessions. Each
entry in the `RECVAL_SESSIONS_DIR/` is a subdirectory named in the
normalized session format. Each subdirectory has `.TextGrid` and `.wav`
files of the recording session.

For example, if I have sessions for 2018-01-01 and 2018-01-07am in
`/data/av/sessions`, then I will have the following line in `.env`:

```sh
RECVAL_SESSIONS_DIR=/data/av/sessions
```

And if I run the following commands, I should see the directory listing
for my sessions directory:

```sh
. .env
ls -F $RECVAL_SESSIONS_DIR
```

    2018-01-01-__-___-_/
    2018-01-07-AM-___-_/

If I then inspect the directory for 2018-01-07am:

```sh
ls
ls -F $RECVAL_SESSIONS_DIR/2018-01-07-AM-___-_/
```

I should get a directory containing files like this.

    Track 2_001.TextGrid
    Track 2_001.wav
    Track 3_001.TextGrid
    Track 3_001.wav
    Track 4_001.TextGrid
    Track 4_001.wav
    ...

**NOTE**: The `*.wav` files may be in a subdirectory called
`${SESSION_NAME}_Recorded`, if the recordings where done with Adobe
Audition. In this example, the `.wav` files would be in
`2018-01-07am_Recorded`.


#### `RECVAL_METADATA_PATH`

This should point to the "Master Recording MetaData" file, obtained from
Google Drive, downloaded as a CSV file. This file is explained more
thoroughly in [Creating the database for the first time][].


#### `RECVAL_AUDIO_DIR`

This is the directory where all the transcoded audio files will be
dumped. During the import process many tiny `*.mp4` files will be
written in this directory. For example, on my computer:

```sh
ls -lh $RECVAL_AUDIO_DIR/
total 21056
-r--r--r--  1 www-data  www-data    19K Oct 31 15:08 004ac84ff9276f7896a6d74acfff47d70d5c738e52c8237905fb0eb62d88f510.m4a
-r--r--r--  1 www-data  www-data    19K Oct 31 15:07 03046963cddbda9812629c78d55f1d3c81706033bd7ee78b2c2e838de1fb3582.m4a
-r--r--r--  1 www-data  www-data    18K Oct 31 15:08 0352ef907a93d0efc1f3f2cf26863d11e90da7211ff1d7cf9c38f4da6cda8d45.m4a
-r--r--r--  1 www-data  www-data    29K Oct 31 15:07 04095b07d0d0a50b974522d4fa336ab762530a6c317a301bb71a4933969aceda.m4a
... thousands of files omited ...
```

For best web serving response time, this directory should be directly
served by the web server (e.g., Apache or Nginx). Place this on a file
system that is fast at reads. It should only be written to when new
recording sessions are imported.

The only required permissions on each file are for reading by the web
server process. The directory must be writable by the import process.


### Creating the database for the first time

[Creating the database for the first time]: #creating-the-database-for-the-first-time

Before you import any data, you need the "Master Recording MetaData"
(sic) spreadsheet, available on Google Drive. Either export this
manually as a CSV file as `$RECVAL_METADATA_PATH`, or, with the
[gdrive][] command installed and configured, run the following script to
download it automatically:

```sh
pipenv run python manage.py downloadmetadata
```

### Importing recordings

In order to import recordings on Sapir, type the following:

```sh
pipenv run python manage.py importrecordings
```

This will automatically scan `$RECVAL_SESSIONS_DIR/` (either set in
`local_settings.py` or as an environment variable).

`$RECVAL_SESSIONS_DIR/` should be a directory filled with directories
(or symbolic links to directories) with filenames in the form of:

    {ISOdate}-{AM/PM}-{Location or '___'}-{Subsession or '_'}

For example, on Sapir, I might have something like this:

    $ export RECVAL_SESSIONS_DIR=/data/av/backup-mwe/sessions
    $ ls -1 $RECVAL_SESSIONS_DIR
    2015-05-08-AM-___-_
    2016-05-16-PM-___-_
    2016-11-28-AM-US-2
    2017-05-25-AM-DS-2
    2018-04-18-AM-KCH-_
    ...

Each directory should have `*.TextGrid` files paired with a `*.wav` file:

    $ ls -F1 $RECVAL_SESSIONS_DIR/2015-05-08-AM-___-_/
    2015-05-08-01.TextGrid
    2015-05-08-01.wav
    2015-05-08-02.TextGrid
    2015-05-08-02.wav
    2015-05-08-03.TextGrid
    2015-05-08-03.wav
    ...


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

Web API
-------

There is one API call:

    /recording/_search/{wordform}

Where `{wordform}` is replaced by a Cree word form, written in SRO.

This will return a JSON array of recordings of that word form.

Each entry in the returned array is a JSON object with the following
properties:

 - **wordform**: the word form that was matched by the query
 - **speaker**: the speaker's short code
 - **gender**: the speaker's gender: either 'M' or 'F'—all our speakers identify as male or female).
 - **recording_url**: Absolute URI to the recording audio (encoded as AAC in an MP4 container).

### Example

Finding recordings of 'nikiskisin':

```http
GET /recording/_search/nikiskisin
```

This will return:

```json
[
    {
        "gender": "F",
        "recording_url": "http://localhost:8000/recording/7353dda3d48799325ee62de0eceb4b50839382cfcf0ebf96c70d84fd37881201.m4a",
        "speaker": "ROS",
        "wordform": "nikiskisin"
    },
    {
        "gender": "F",
        "recording_url": "http://localhost:8000/recording/dac08c374354594b7a77195daa4fd2e12a88acc5acf4e4894dd612354c1e7a92.m4a",
        "speaker": "ROS",
        "wordform": "nikiskisin"
    },
    {
        "gender": "M",
        "recording_url": "http://localhost:8000/recording/1576034645a6b765ab40275a67390fa197ee3c7ed8cc949907d132df3c0f1c9e.m4a",
        "speaker": "GOR",
        "wordform": "nikiskisin"
    },
    {
        "gender": "M",
        "recording_url": "http://localhost:8000/recording/a86939d888ff908d091538b2c1a3dc4fb383167b781b5dddddd4253342b0dace.m4a",
        "speaker": "GOR",
        "wordform": "nikiskisin"
    },
    {
        "gender": "F",
        "recording_url": "http://localhost:8000/recording/2198ff134107ff474115cdb48ee36f88c17168e215fe424da4cc414bab0f4582.m4a",
        "speaker": "LOU",
        "wordform": "nikiskisin"
    },
    {
        "gender": "F",
        "recording_url": "http://localhost:8000/recording/e8dd10846601861c1e9c4edf944b1e4da7670ed669fe027bd0b27e0af954e031.m4a",
        "speaker": "LOU",
        "wordform": "nikiskisin"
    }
]
```


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
