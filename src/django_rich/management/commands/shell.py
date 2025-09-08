from __future__ import annotations

from typing import Any

from django.core.management.commands.shell import Command as BaseCommand
from rich import pretty


class Command(BaseCommand):
    def handle(self, **options: Any) -> None:
        pretty.install()
        return super().handle(**options)

    def get_auto_imports(self) -> list[str]:
        auto_imports: list[str] = super().get_auto_imports()  # type: ignore[misc]
        auto_imports.append("rich.inspect")
        auto_imports.append("rich.print")
        auto_imports.append("rich.print_json")
        auto_imports.append("rich.pretty.pprint")
        return auto_imports
