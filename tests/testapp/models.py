from __future__ import annotations

from django.db import models


class Person(models.Model):
    class Meta:
        app_label = "testapp"

    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
