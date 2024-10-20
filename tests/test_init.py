from __future__ import annotations

from django.db.models import Sum
from django.db.models.functions import Length
from django.test import TestCase
from django.test.utils import captured_stdout

from django_rich import tabulate

from .testapp.models import Person


class TabulateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Person.objects.create(id=1, name="Ash", age=10)
        Person.objects.create(id=2, name="Misty", age=10)
        Person.objects.create(id=3, name="Professor Oak", age=50)

    def test_dict_empty(self):
        with captured_stdout() as stdout:
            tabulate({})
        lines = stdout.getvalue().splitlines()
        assert lines == [""]

    def test_dict_from_aggregate(self):
        with captured_stdout() as stdout:
            tabulate(Person.objects.aggregate(Sum("age")))
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "┏━━━━━━━━━━┓",
            "┃ age__sum ┃",
            "┡━━━━━━━━━━┩",
            "│ 70       │",
            "└──────────┘",
        ]

    def test_values(self):
        with captured_stdout() as stdout:
            tabulate(Person.objects.values("name"))
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "     People      ",
            "┏━━━━━━━━━━━━━━━┓",
            "┃ name          ┃",
            "┡━━━━━━━━━━━━━━━┩",
            "│ Ash           │",
            "│ Misty         │",
            "│ Professor Oak │",
            "└───────────────┘",
        ]

    def test_values_with_annotation(self):
        with captured_stdout() as stdout:
            tabulate(Person.objects.values("name").annotate(len=Length("name")))
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "        People         ",
            "┏━━━━━━━━━━━━━━━┳━━━━━┓",
            "┃ name          ┃ len ┃",
            "┡━━━━━━━━━━━━━━━╇━━━━━┩",
            "│ Ash           │ 3   │",
            "│ Misty         │ 5   │",
            "│ Professor Oak │ 13  │",
            "└───────────────┴─────┘",
        ]

    def test_values_elided(self):
        with captured_stdout() as stdout:
            tabulate(Person.objects.values("name"), limit=1)
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "       People       ",
            "┏━━━━━━━━━━━━━━━━━━┓",
            "┃ name             ┃",
            "┡━━━━━━━━━━━━━━━━━━┩",
            "│ Ash              │",
            "│ …                │",
            "└──────────────────┘",
            "   1 of 3 records   ",
            "     shown. Use     ",
            "`limit=None` to show",
            "    all records.    ",
        ]

    def test_queryset_empty(self):
        with captured_stdout() as stdout:
            tabulate(Person.objects.none())
        assert stdout.getvalue() == "Empty QuerySet.\n"

    def test_queryset(self):
        with captured_stdout() as stdout:
            tabulate(Person.objects.all())
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "           People           ",
            "┏━━━━┳━━━━━━━━━━━━━━━┳━━━━━┓",
            "┃ id ┃ name          ┃ age ┃",
            "┡━━━━╇━━━━━━━━━━━━━━━╇━━━━━┩",
            "│ 1  │ Ash           │ 10  │",
            "│ 2  │ Misty         │ 10  │",
            "│ 3  │ Professor Oak │ 50  │",
            "└────┴───────────────┴─────┘",
        ]

    def test_elided(self):
        with captured_stdout() as stdout:
            tabulate(Person.objects.all(), limit=1)
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "       People       ",
            "┏━━━━━┳━━━━━━┳━━━━━┓",
            "┃ id  ┃ name ┃ age ┃",
            "┡━━━━━╇━━━━━━╇━━━━━┩",
            "│ 1   │ Ash  │ 10  │",
            "│ …   │ …    │ …   │",
            "└─────┴──────┴─────┘",
            "   1 of 3 records   ",
            "     shown. Use     ",
            "`limit=None` to show",
            "    all records.    ",
        ]

    def test_single_value(self):
        with captured_stdout() as stdout:
            tabulate(Person.objects.count())
        lines = stdout.getvalue().splitlines()
        assert lines == ["3"]

    def test_only(self):
        with captured_stdout() as stdout:
            tabulate(Person.objects.all().only("age"))
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "People ",
            "┏━━━━━┓",
            "┃ age ┃",
            "┡━━━━━┩",
            "│ 10  │",
            "│ 10  │",
            "│ 50  │",
            "└─────┘",
        ]

    def test_defer(self):
        with captured_stdout() as stdout:
            tabulate(Person.objects.all().defer("age"))
        lines = stdout.getvalue().splitlines()
        assert lines == [
            "        People        ",
            "┏━━━━┳━━━━━━━━━━━━━━━┓",
            "┃ id ┃ name          ┃",
            "┡━━━━╇━━━━━━━━━━━━━━━┩",
            "│ 1  │ Ash           │",
            "│ 2  │ Misty         │",
            "│ 3  │ Professor Oak │",
            "└────┴───────────────┘",
        ]
