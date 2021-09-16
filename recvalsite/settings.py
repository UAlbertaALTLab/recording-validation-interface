"""
Django settings for recvalsite project.

Generated by 'django-admin startproject' using Django 2.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import secrets
from pathlib import Path

from decouple import config

from .save_secret_key import save_secret_key

# Build paths inside the project like this: BASE_DIR / 'path' / 'to' / 'file'
BASE_DIR = Path(__file__).resolve().parent.parent
assert (BASE_DIR / "manage.py").is_file()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default=None)
if SECRET_KEY is None:
    SECRET_KEY = save_secret_key(secrets.token_hex())


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False, cast=bool)
USE_DJANGO_DEBUG_TOOLBAR = config("USE_DJANGO_DEBUG_TOOLBAR", default=DEBUG, cast=bool)

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "speech-db.altlab.app", "altlab-itw:8004"]


# Application definition

INSTALLED_APPS = [
    # Apps defined in this repository.
    "validation",
    "media_with_range.apps.MediaWithRangeConfig",
    # Django built-in apps.
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Dependencies.
    "simple_history",
]

# Apps used only during debug mode
if DEBUG:
    INSTALLED_APPS.append("django_extensions")
    if USE_DJANGO_DEBUG_TOOLBAR:
        INSTALLED_APPS.append("debug_toolbar")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Automatically insert user that changed a model with history.
    "simple_history.middleware.HistoryRequestMiddleware",
]

if DEBUG and USE_DJANGO_DEBUG_TOOLBAR:
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = "recvalsite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "recvalsite.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

# Where to place the SQLite3 database file:
RECVAL_SQLITE_DB_PATH = config(
    "RECVAL_SQLITE_DB_PATH", default=BASE_DIR / "db.sqlite3", cast=Path
)


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.fspath(RECVAL_SQLITE_DB_PATH),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-CA"

TIME_ZONE = "America/Edmonton"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Templates
# https://docs.djangoproject.com/en/2.1/ref/settings/#templates
# https://docs.djangoproject.com/en/2.1/topics/templates/#django.template.backends.jinja2.Jinja2
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"environment": "validation.jinja2.environment"},
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    },
]

# Security
# Should we send the X-XSS-Protection header
SECURE_BROWSER_XSS_FILTER = True
# Should the browser NOT try to detect the content type of unmarked content?
SECURE_CONTENT_TYPE_NOSNIFF = True
# Should we allow hosting in an <iframe>?
X_FRAME_OPTIONS = "DENY"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/static/"

# Remember to run manage.py collectstatic!
default_static_dir = "/var/www/recvalsite/static"
if DEBUG:
    default_static_dir = BASE_DIR / "static"
STATIC_ROOT = config("STATIC_ROOT", default=default_static_dir)

# This is concatenated with MEDIA_ROOT and MEDIA_URL to store and serve the audio files.
RECVAL_AUDIO_PREFIX = config("RECVAL_AUDIO_PREFIX", default="audio/")
BIO_INFO_PREFIX = config("BIO_INFO_PREFIX", default="data/speakers/biographies")

# Where to find the metadata CSV file.
RECVAL_METADATA_PATH = config(
    "RECVAL_METADATA_PATH", BASE_DIR / "private" / "metadata.csv", cast=Path
)

TSUUTINA_METADATA_PATH = config(
    "TSUUTINA_METADATA_PATH", BASE_DIR / "private" / "tsuutina-metadata.csv", cast=Path
)

# Where the sessions should be extracted from.
# Expecting a structure like this:
#
# ${RECVAL_SESSIONS_DIR}/
# ├── 2015-10-04-AM-KCH-2/
# ├── ...
# └── 2016-01-18-PM-___-_/
RECVAL_SESSIONS_DIR = config(
    "RECVAL_SESSIONS_DIR", BASE_DIR / "data" / "sessions", cast=Path
)

TSUUTINA_SESSIONS_DIR = config(
    "TSUUTINA_SESSIONS_DIR", BASE_DIR / "data" / "tsuutina", cast=Path
)

################################### MEDIA (Uploads) ####################################

# Audio (including compressed recordings) and pictures are uploaded here.
# See: https://docs.djangoproject.com/en/2.2/topics/files/

# This is the default media path; however, you will want to choose something different!
MEDIA_URL = config("MEDIA_URL", default="/media/")

# Recoring URLS will be moved here
MEDIA_ROOT = config("MEDIA_ROOT", default=BASE_DIR / "data", cast=str)

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login"

ITWEWINA_URL = "https://itwewina.altlab.app/"

FIXTURE_DIRS = (BASE_DIR / "validation" / "management" / "fixtures",)

INTERNAL_IPS = ["127.0.0.1"]

log_level = "INFO"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            # The handler should print anything that gets to it, so that
            # debugging can be enabled for specific loggers without also turning
            # on debug loggers for all of django/python
            "level": "NOTSET",
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": log_level,
    },
    "loggers": {
        # learn how different loggers are used in Django: https://docs.djangoproject.com/en/3.0/topics/logging/#id3
        "django": {
            "handlers": [],
            "level": log_level,
            "propagate": True,
        },
    },
}

ADMINS = [("Jolene", "jcpoulin@ualberta.ca")]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = config("SMTP_USER", default=None)
EMAIL_HOST_PASSWORD = config("SMTP_PASS", default=None)
EMAIL_USE_TLS = True
