from __future__ import annotations

from typing import Any

SECRET_KEY = "NOTASECRET"

ALLOWED_HOSTS: list[str] = []

DATABASES: dict[str, dict[str, Any]] = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'testdb',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS = [
    "tests.testapp",
]

MIDDLEWARE: list[str] = []

TEST_RUNNER = "django_rich.test.RichRunner"

USE_TZ = True
