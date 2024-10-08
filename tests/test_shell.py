from __future__ import annotations

import sys
from code import InteractiveConsole
from unittest import mock

import faker
import pytest
from django.core.management import call_command
from django.db.models import Sum
from django.db.models.functions import Length
from django.test import SimpleTestCase
from django.test import TestCase
from django.test.utils import captured_stdin
from django.test.utils import captured_stdout
from factory import lazy_attribute
from factory.django import DjangoModelFactory

from django_rich.table import tabulate_qs

from .testapp.models import Person

faker = faker.Factory.create()


class PersonFactory(DjangoModelFactory):  # type: ignore [misc]
    class Meta:
        model = "testapp.Person"

    name = lazy_attribute(lambda o: faker.name())  # pragma: no cover
    age = lazy_attribute(lambda o: faker.random_number(digits=2))  # pragma: no cover


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
        assert lines == [
            "╭─────╮",
            "│ hi! │",
            "╰─────╯",
        ]


class QuerySetTests(TestCase):
    def test_tabulate_qs(self):
        PersonFactory(name="Test Name", age=8)
        PersonFactory(name="Another Name", age=88)
        with captured_stdout() as stdout:
            tabulate_qs(Person.objects.all())
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "         Person(s)         ",
            "┏━━━━┳━━━━━━━━━━━━━━┳━━━━━┓",
            "┃ id ┃ name         ┃ age ┃",
            "┡━━━━╇━━━━━━━━━━━━━━╇━━━━━┩",
            "│ 1  │ Test Name    │ 8   │",
            "│ 2  │ Another Name │ 88  │",
            "└────┴──────────────┴─────┘",
        ]

    def test_tabulate_qs_elided(self):
        PersonFactory(name="Test Name", age=8)
        PersonFactory(name="Another Name", age=88)
        with captured_stdout() as stdout:
            tabulate_qs(Person.objects.all(), limit=1)
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "       Person(s)        ",
            "┏━━━━┳━━━━━━━━━━━┳━━━━━┓",
            "┃ id ┃ name      ┃ age ┃",
            "┡━━━━╇━━━━━━━━━━━╇━━━━━┩",
            "│ 1  │ Test Name │ 8   │",
            "│ …  │ …         │ …   │",
            "└────┴───────────┴─────┘",
            " 1 of 2 records shown.  ",
            "Use `limit=None` to show",
            "      all records.      ",
        ]

    def test_tabulate_qs_single_value(self):
        PersonFactory(name="Test Name", age=8)
        with captured_stdout() as stdout:
            tabulate_qs(Person.objects.count())
        lines = stdout.getvalue().splitlines()
        assert lines == ["1"]

    def test_tabulate_dict(self):
        PersonFactory(name="Test Name", age=8)
        PersonFactory(name="Another Name", age=88)
        with captured_stdout() as stdout:
            tabulate_qs(Person.objects.aggregate(Sum("age")))
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "┏━━━━━━━━━━┓",
            "┃ age__sum ┃",
            "┡━━━━━━━━━━┩",
            "│ 96       │",
            "└──────────┘",
        ]

    def test_tabulate_qs_dict(self):
        PersonFactory(name="Test Name", age=8)
        PersonFactory(name="Another Name", age=88)
        with captured_stdout() as stdout:
            tabulate_qs(Person.objects.values("name").annotate(len=Length("age")))
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "      Person(s)       ",
            "┏━━━━━━━━━━━━━━┳━━━━━┓",
            "┃ name         ┃ len ┃",
            "┡━━━━━━━━━━━━━━╇━━━━━┩",
            "│ Test Name    │ 1   │",
            "│ Another Name │ 2   │",
            "└──────────────┴─────┘",
        ]

    def test_empty_queryset(self):
        with captured_stdout() as stdout:
            tabulate_qs(Person.objects.all())
        assert stdout.getvalue() == "\n"

    def test_only(self):
        PersonFactory(name="Test Name", age=8)
        with captured_stdout() as stdout:
            tabulate_qs(Person.objects.all().only("age"))
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "Person(",
            "  s)   ",
            "┏━━━━━┓",
            "┃ age ┃",
            "┡━━━━━┩",
            "│ 8   │",
            "└─────┘",
        ]

    def test_defer(self):
        PersonFactory(name="Test Name", age=8)
        with captured_stdout() as stdout:
            tabulate_qs(Person.objects.all().defer("age"))
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "    Person(s)     ",
            "┏━━━━┳━━━━━━━━━━━┓",
            "┃ id ┃ name      ┃",
            "┡━━━━╇━━━━━━━━━━━┩",
            "│ 1  │ Test Name │",
            "└────┴───────────┘",
        ]
