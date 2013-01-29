# Copyright 2013 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os

ROOT = os.path.abspath(os.path.dirname(__file__))
DEBUG = int(os.environ.get("MYSQLAPI_DEBUG", 1)) != 0
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("MYSQLAPI_DB_NAME", "mysqlapi"),
        "USER": os.environ.get("MYSQLAPI_DB_USER", "root"),
        "PASSWORD": os.environ.get("MYSQLAPI_DB_PASSWORD", ""),
        "HOST": os.environ.get("MYSQLAPI_HOST", "localhost"),
        "PORT": "",
        "TEST_NAME": "test_api",
    }
}

TIME_ZONE = "America/Chicago"

LANGUAGE_CODE = "en-us"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ""

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ""

# Absolute path to the directory static files should be collected to.
# Don"t put anything in this directory yourself; store your static files
# in apps" "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ""

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/static/"

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don"t forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# Make this unique, and don"t share it with anybody.
SECRET_KEY = "i8$33=vy4@n%q!d@&amp;mj$jsr)r7q6b9@f0301!hqp7f1)i4npg8"

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)

MIDDLEWARE_CLASSES = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # Uncomment the next line for simple clickjacking protection:
    # "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

ROOT_URLCONF = "mysqlapi.urls"

# Python dotted path to the WSGI application used by Django"s runserver.
WSGI_APPLICATION = "wsgi.application"

TEMPLATE_DIRS = (
    os.path.join(ROOT, "templates"),
)

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "mysqlapi.api",
    # Uncomment the next line to enable the admin:
    # "django.contrib.admin",
    # Uncomment the next line to enable admin documentation:
    # "django.contrib.admindocs",
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
    }
}

RESERVED_NAMES = ("mysql", "test", "information_schema", "mysqlapi")
SHARED_SERVER = os.environ.get("MYSQLAPI_SHARED_SERVER")
SHARED_SERVER_PUBLIC_HOST = os.environ.get(
    "MYSQLAPI_SHARED_SERVER_PUBLIC_HOST",
    SHARED_SERVER,
)
SHARED_USER = os.environ.get("MYSQLAPI_SHARED_USER", "root")
SHARED_PASSWORD = os.environ.get("MYSQLAPI_SHARED_PASSWORD", "")

EC2_ENDPOINT = os.environ.get("MYSQLAPI_EC2_ENDPOINT")
EC2_PORT = os.environ.get("MYSQLAPI_EC2_PORT")
EC2_PATH = os.environ.get("MYSQLAPI_EC2_PATH")
EC2_ACCESS_KEY = os.environ.get("MYSQLAPI_EC2_ACCESS_KEY")
EC2_SECRET_KEY = os.environ.get("MYSQLAPI_EC2_SECRET_KEY")
EC2_AMI = os.environ.get("MYSQLAPI_EC2_AMI")
EC2_KEY_NAME = os.environ.get("MYSQLAPI_EC2_KEY_NAME")
EC2_POLL_INTERVAL = int(os.environ.get("MYSQLAPI_EC2_POLL_INTERVAL", 10))

TEST_RUNNER = 'mysqlapi.runner.DiscoveryRunner'

S3_ACCESS_KEY = os.environ.get("TSURU_S3_ACCESS_KEY_ID")
S3_SECRET_KEY = os.environ.get("TSURU_S3_SECRET_KEY")
S3_BUCKET = os.environ.get("TSURU_S3_BUCKET")

SALT = os.environ.get("MYSQLAPI_SALT", "")
