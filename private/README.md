Configuration files for deploying on Sapir
==========================================

These files configure the application on Sapir:

    .
    ├── apache2.4
    │   └── sites-available
    │       └── validation.conf
    └── systemd
        └── system
            └── recval.service.template

> **NOTE**: you will have to customize `recval.service.template` to
> create `recval.service`.

Once they're copied and configured in the right places, then this should
get the service up and running:

    sudo service recval start
    sudo apachectl reload


Other files
-----------

I didn't have a good place for these files, so they're in this
directory:

clean-dir-structure.py
 : Reorganizes /data/av/backup-mwe to a clean directory structure in
  /data/av/backup-mwe with systematic folder names. It does this in
  a **non-destructive** manner by creating symbolic links. Much of this
  code is duplcated from recval/extract_phrases.py and
  recval/recording_session.py.

metadata.csv
 : This is the CSV export of "Master Recordings MetaData" from Google
  Drive.

phrases.sql
 : An experimental query for creating a denormalized copy of the
  database (such as to export to a CSV file or to use within R).
