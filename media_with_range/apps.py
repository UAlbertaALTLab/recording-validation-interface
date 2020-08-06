#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from django.apps import AppConfig  # type: ignore


class MediaWithRangeConfig(AppConfig):
    name = "media_with_range"
    verbose_name = "Server media with support for Range requests"
