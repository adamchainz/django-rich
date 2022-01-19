from __future__ import annotations

from django_rich.management import RichCommand


class Command(RichCommand):
    def handle(self, *args, **options):
        self.console.print("[bold red]Alert![/bold red]")
