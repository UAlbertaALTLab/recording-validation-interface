#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright © 2018 Eddie Antonio Santos. All rights reserved.

from flask import Flask  # type: ignore


app = Flask(__name__)


@app.route('/')
def hello():
    return '<h1> Hello, World </h1>'
