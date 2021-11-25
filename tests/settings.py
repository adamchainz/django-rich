from typing import Any, Dict, List

SECRET_KEY = "NOTASECRET"

ALLOWED_HOSTS: List[str] = []

DATABASES: Dict[str, Dict[str, Any]] = {}

INSTALLED_APPS = [
    "tests.testapp",
]

MIDDLEWARE: List[str] = []

USE_TZ = True
