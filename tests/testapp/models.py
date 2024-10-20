from __future__ import annotations

from django.db import models


class Person(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()

    class Meta:
        verbose_name = "person"
        verbose_name_plural = "people"
