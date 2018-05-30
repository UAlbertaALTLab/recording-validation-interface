Configuration files for deploying on Sapir
==========================================

These files configure the application on Sapir:

.
├── apache2.4
│   └── sites-available
│       └── recval.conf
└── systemd
    └── system
        └── recval.service  

Once they're copied into the right places, then this should get the
service up and running:

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
  Drive. If it does not exist, use `flask metadata download` to download
  the latest copy. Note: requires a properly configured [gdrive][]
  executable on the path.

phrases.sql
 : An experimental query for creating a denormalized copy of the
  database (such as to export to a CSV file or to use within R).


[gdrive]: https://github.com/prasmussen/gdrive
