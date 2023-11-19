# -*- coding: utf-8 -*-
from realjournals.settings import * # noqa, pylint: disable=unused-wildcard-import

DEBUG = True

ENABLE_TELEMETRY = False

SECRET_KEY = "not very secret in tests"

TEMPLATES[0]["OPTIONS"]['context_processors'] += "django.template.context_processors.debug"

CELERY_ENABLED = False

MEDIA_ROOT = "/tmp"

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
INSTALLED_APPS = INSTALLED_APPS + [
    "tests",
]

FRONT_SITEMAP_ENABLED = True
FRONT_SITEMAP_CACHE_TIMEOUT = 1  # In second
FRONT_SITEMAP_PAGE_SIZE = 100

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'realjournals',
        'USER': 'realjournals',
        'PASSWORD': 'realjournals',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# This is only for GitHubActions
if os.getenv('GITHUB_WORKFLOW'):
    DATABASES = {
        'default': {
            "ENGINE": "django.db.backends.postgresql",
            'NAME': 'realjournals',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }