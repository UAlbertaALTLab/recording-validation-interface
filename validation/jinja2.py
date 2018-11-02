#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Adpated from: https://medium.com/@samuh/using-jinja2-with-django-1-8-onwards-9c58fe1204dc

from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        # Enables use of {% static ... %}
        'static': staticfiles_storage.url,
        # Enables use of {% url ... %}
        'url': reverse,
    })
    return env
