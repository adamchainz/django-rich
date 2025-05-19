from __future__ import annotations

import sys
from code import InteractiveConsole
from unittest import mock

import django
import pytest
from django.core.management import call_command
from django.test import SimpleTestCase
from django.test.utils import captured_stdin, captured_stdout


class ShellCommandTestCase(SimpleTestCase):
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows select() doesn't support file descriptors.",
    )
    @mock.patch("django.core.management.commands.shell.select")
    def test_pretty(self, select):
        console = InteractiveConsole()
        with captured_stdin() as _, captured_stdout() as stdout:
            call_command("shell", "-i", "python")
            console.push("from rich.panel import Panel\n")
            console.push('Panel.fit("hi!")\n')
        lines = stdout.getvalue().splitlines()
        if django.VERSION >= (5, 2):
            assert lines == [
                "0 objects imported automatically.",
                "",
                "╭─────╮",
                "│ hi! │",
                "╰─────╯",
            ]
        else:
            assert lines == [
                "╭─────╮",
                "│ hi! │",
                "╰─────╯",
            ]
