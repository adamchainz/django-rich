from functools import partial
from inspect import Parameter, Signature, signature
from io import StringIO
from unittest import mock

import pytest
from django.core.management import BaseCommand, CommandError, call_command
from django.test import SimpleTestCase
from rich.console import Console

from django_rich.management import RichCommand
from tests.testapp.management.commands.example import Command as ExampleCommand


def strip_annotations(original: Signature) -> Signature:
    return Signature(
        parameters=[
            param.replace(annotation=Parameter.empty)
            for param in original.parameters.values()
        ]
    )


class FakeTtyStringIO(StringIO):
    def isatty(self) -> bool:
        return True


class RichCommandTests(SimpleTestCase):
    def test_init_signature(self):
        rc_signature = strip_annotations(signature(RichCommand.__init__))

        assert rc_signature == signature(BaseCommand.__init__)

    def test_execute_signature(self):
        rc_signature = strip_annotations(signature(RichCommand.execute))

        assert rc_signature == signature(BaseCommand.execute)

    def test_combined_color_flags_error(self):
        with pytest.raises(CommandError) as excinfo:
            call_command("example", "--no-color", "--force-color")

        assert (
            str(excinfo.value)
            == "The --no-color and --force-color options can't be used together."
        )

    def test_output_non_tty(self):
        stdout = StringIO()

        call_command("example", stdout=stdout)

        assert stdout.getvalue() == "Alert!\n"

    def test_output_tty(self):
        stdout = FakeTtyStringIO()

        call_command("example", stdout=stdout)

        assert stdout.getvalue() == "\x1b[1;31mAlert!\x1b[0m\n"

    def test_output_tty_no_color(self):
        stdout = FakeTtyStringIO()

        call_command("example", "--no-color", stdout=stdout)

        assert stdout.getvalue() == "Alert!\n"

    def test_output_force_color(self):
        stdout = StringIO()

        call_command("example", "--force-color", stdout=stdout)

        assert stdout.getvalue() == "\x1b[1;31mAlert!\x1b[0m\n"

    def test_output_make_rich_console(self):
        stdout = FakeTtyStringIO()
        make_console = partial(Console, markup=False, highlight=False)
        patcher = mock.patch.object(ExampleCommand, "make_rich_console", make_console)

        with patcher:
            call_command("example", stdout=stdout)

        assert stdout.getvalue() == "[bold red]Alert![/bold red]\n"
