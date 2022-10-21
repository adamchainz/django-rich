from __future__ import annotations

import sys
from code import InteractiveConsole
from textwrap import dedent
from unittest import mock

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
            call_command("shell")
            console.push(
                dedent(
                    """
                    test = {
                        "foo": [1, 2, 3, (4, 5, {6}, 7, 8, {9}), {}],
                        "bar": {"egg": "baz", "words": ["Hello World"] * 10},
                        False: "foo",
                        True: "",
                        "text": ("Hello World", "foo bar baz egg"),
                    }
                    """
                )
            )
            console.push("test\n")
        assert (
            stdout.getvalue().strip()
            == "{\n    'foo': [1, 2, 3, (4, 5, {6}, 7, 8, {9}), {}],\n    'bar':"
            " {\n        'egg': 'baz',\n        'words': [\n            'Hello"
            " World',\n            'Hello World',\n            'Hello World',\n"
            "            'Hello World',\n            'Hello World',\n          "
            "  'Hello World',\n            'Hello World',\n            'Hello "
            "World',\n            'Hello World',\n            'Hello World'\n  "
            "      ]\n    },\n    False: 'foo',\n    True: '',\n    'text':"
            " ('Hello World', 'foo bar baz egg')\n}"
        )
