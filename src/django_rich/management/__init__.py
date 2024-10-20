from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any
from typing import TextIO

from django.core.management import BaseCommand
from django.core.management import CommandError
from rich.console import Console


class RichCommand(BaseCommand):
    def __init__(
        self,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
        no_color: bool = False,
        force_color: bool = False,
    ):
        super().__init__(stdout, stderr, no_color, force_color)
        self._setup_console(stdout, no_color, force_color)

    def execute(self, *args: Any, **options: Any) -> str | None:
        force_color: bool = options["force_color"]
        no_color: bool = options["no_color"]
        stdout: TextIO | None = options.get("stdout")

        # Duplicate check from Django, since we’re running first.
        if force_color and no_color:
            raise CommandError(
                "The --no-color and --force-color options can't be used together."
            )

        self._setup_console(stdout, no_color, force_color)

        return super().execute(*args, **options)

    def _setup_console(
        self,
        stdout: TextIO | None,
        no_color: bool | None,
        force_color: bool | None,
    ) -> None:
        force_terminal: bool | None = None
        if no_color:
            force_terminal = False
        elif force_color:
            force_terminal = True

        self.console = self.make_rich_console(
            file=(stdout or sys.stdout),
            force_terminal=force_terminal,
        )

    make_rich_console: Callable[..., Console] = Console
