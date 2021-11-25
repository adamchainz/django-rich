import sys
from typing import IO, Any, Optional

from django.core.management import BaseCommand, CommandError
from rich.console import Console


class RichCommand(BaseCommand):
    def __init__(
        self,
        stdout: Optional[IO[str]] = None,
        stderr: Optional[IO[str]] = None,
        no_color: Optional[bool] = False,
        force_color: Optional[bool] = False,
    ):
        super().__init__(stdout, stderr, no_color, force_color)
        self._setup_console(stdout, no_color, force_color)

    def execute(self, *args: Any, **options: Any) -> Optional[str]:
        force_color: Optional[bool] = options["force_color"]
        no_color: Optional[bool] = options["no_color"]
        stdout: Optional[IO[str]] = options.get("stdout")

        # Duplicate check from Django, since we’re running first.
        if force_color and no_color:
            raise CommandError(
                "The --no-color and --force-color options can't be used together."
            )

        self._setup_console(stdout, no_color, force_color)

        return super().execute(*args, **options)

    def _setup_console(
        self,
        stdout: Optional[IO[str]],
        no_color: Optional[bool],
        force_color: Optional[bool],
    ) -> None:
        force_terminal: Optional[bool] = None
        if no_color:
            force_terminal = False
        elif force_color:
            force_terminal = True

        self.console = self.make_rich_console(
            file=(stdout or sys.stdout),
            force_terminal=force_terminal,
        )

    make_rich_console = Console
