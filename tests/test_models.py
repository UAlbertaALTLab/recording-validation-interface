#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


# Based on http://alextechrants.blogspot.ca/2013/08/unit-testing-sqlalchemy-apps.html

from sqlalchemy.engine import create_engine  # type: ignore
from sqlalchemy.orm.session import Session  # type: ignore

from recval.app import Model, Word, Sentence, Recording  # This is your declarative base class


def setup_module():
    global transaction, connection, engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine('postgresql:///yourdb')
    connection = engine.connect()
    transaction = connection.begin()
    Base.metadata.create_all(connection)

    # If you want to insert fixtures to the DB, do it here


def teardown_module():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()


class DatabaseTest:
    def setup(self):
        self.__transaction = connection.begin_nested()
        self.session = Session(connection)

    def teardown(self):
        self.session.close()
        self.__transaction.rollback()
