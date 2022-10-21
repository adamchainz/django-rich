from __future__ import annotations

from typing import Any

from django.core.management.commands.shell import Command as BaseCommand
from rich import pretty


class Command(BaseCommand):
    def handle(self, **options: Any) -> str | None:
        pretty.install()
        return super().handle(**options)
