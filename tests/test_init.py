from __future__ import annotations

import faker
from django.db.models import Sum
from django.db.models.functions import Length
from django.test import TestCase
from django.test.utils import captured_stdout
from factory import lazy_attribute
from factory.django import DjangoModelFactory

from django_rich import tabulate

from .testapp.models import Person

faker = faker.Factory.create()


class PersonFactory(DjangoModelFactory):  # type: ignore [misc]
    class Meta:
        model = "testapp.Person"

    name = lazy_attribute(lambda o: faker.name())  # pragma: no cover
    age = lazy_attribute(lambda o: faker.random_number(digits=2))  # pragma: no cover


class TabulateTests(TestCase):
    def test_queryset(self):
        PersonFactory(name="Test Name", age=8)
        PersonFactory(name="Another Name", age=88)
        with captured_stdout() as stdout:
            tabulate(Person.objects.all())
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

    def test_elided(self):
        PersonFactory(name="Test Name", age=8)
        PersonFactory(name="Another Name", age=88)
        with captured_stdout() as stdout:
            tabulate(Person.objects.all(), limit=1)
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

    def test_single_value(self):
        PersonFactory(name="Test Name", age=8)
        with captured_stdout() as stdout:
            tabulate(Person.objects.count())
        lines = stdout.getvalue().splitlines()
        assert lines == ["1"]

    def test_dict(self):
        PersonFactory(name="Test Name", age=8)
        PersonFactory(name="Another Name", age=88)
        with captured_stdout() as stdout:
            tabulate(Person.objects.aggregate(Sum("age")))
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "┏━━━━━━━━━━┓",
            "┃ age__sum ┃",
            "┡━━━━━━━━━━┩",
            "│ 96       │",
            "└──────────┘",
        ]

    def test_annotation(self):
        PersonFactory(name="Test Name", age=8)
        PersonFactory(name="Another Name", age=88)
        with captured_stdout() as stdout:
            tabulate(Person.objects.values("name").annotate(len=Length("age")))
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
            tabulate(Person.objects.all())
        assert stdout.getvalue() == "\n"

    def test_only(self):
        PersonFactory(name="Test Name", age=8)
        with captured_stdout() as stdout:
            tabulate(Person.objects.all().only("age"))
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
            tabulate(Person.objects.all().defer("age"))
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "    Person(s)     ",
            "┏━━━━┳━━━━━━━━━━━┓",
            "┃ id ┃ name      ┃",
            "┡━━━━╇━━━━━━━━━━━┩",
            "│ 1  │ Test Name │",
            "└────┴───────────┘",
        ]
