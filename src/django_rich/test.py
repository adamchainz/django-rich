from __future__ import annotations

import io
import sys
import unittest
from types import TracebackType
from typing import Tuple, Type, Union
from unittest.case import TestCase
from unittest.result import (  # type: ignore [attr-defined]
    STDERR_LINE,
    STDOUT_LINE,
    failfast,
)

import django
from django.test import testcases
from django.test.runner import DebugSQLTextTestResult, DiscoverRunner
from rich.color import Color
from rich.console import Console
from rich.rule import Rule
from rich.style import Style
from rich.traceback import Traceback

if django.VERSION >= (3, 0):
    from django.test.runner import PDBDebugResult


_SysExcInfoType = Union[
    Tuple[Type[BaseException], BaseException, TracebackType],
    Tuple[None, None, None],
]

DJANGO_GREEN = Style(color=Color.from_rgb(32, 170, 118))


class RichTextTestResult(unittest.TextTestResult):
    # Declaring attribute since typeshed had wrong capitalization
    # https://github.com/python/typeshed/pull/7340
    showAll: bool

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.console = Console(
            file=self.stream.stream,  # Normally sys.stderr
        )

    def addSuccess(self, test: TestCase) -> None:
        if self.showAll:
            self.console.print("ok", style=DJANGO_GREEN)
        elif self.dots:
            self.console.print(".", style=DJANGO_GREEN, end="")

    @failfast
    def addError(self, test: TestCase, err: _SysExcInfoType) -> None:
        self.errors.append((test, self._exc_info_to_string(err, test)))
        self._mirrorOutput = True
        if self.showAll:
            self.console.print("ERROR", style=Style(color="red"))
        elif self.dots:
            self.console.print("E", style=Style(color="red"), end="")

    @failfast
    def addFailure(self, test: TestCase, err: _SysExcInfoType) -> None:
        self.failures.append((test, self._exc_info_to_string(err, test)))
        self._mirrorOutput = True
        if self.showAll:
            self.console.print("FAIL", style=Style(color="red"))
        elif self.dots:
            self.console.print("F", style=Style(color="red"), end="")

    def addSkip(self, test: TestCase, reason: str) -> None:
        self.skipped.append((test, reason))
        if self.showAll:
            self.console.print(f"skipped {reason!r}", style=Style(color="yellow"))
        elif self.dots:
            self.console.print("s", style=Style(color="yellow"), end="")

    def addExpectedFailure(self, test: TestCase, err: _SysExcInfoType) -> None:
        self.expectedFailures.append((test, self._exc_info_to_string(err, test)))
        if self.showAll:
            self.console.print("expected failure", style=Style(color="yellow"))
        elif self.dots:
            self.console.print("x", style=Style(color="yellow"), end="")

    @failfast
    def addUnexpectedSuccess(self, test: TestCase) -> None:
        self.unexpectedSuccesses.append(test)
        if self.showAll:
            self.console.print("unexpected success", style=Style(color="red"))
        elif self.dots:
            self.console.print("u", style=Style(color="red"), end="")

    # Typeshed had wrong signature
    # https://github.com/python/typeshed/pull/7341
    def printErrorList(  # type: ignore [override]
        self,
        flavour: str,
        errors: list[tuple[TestCase, str]],
    ) -> None:
        for test, err in errors:
            rule = Rule(style=DJANGO_GREEN)
            title = f"{flavour}: {self.getDescription(test)}"
            self.console.print(rule, title, rule)
            self.stream.write("%s\n" % err)

    def _exc_info_to_string(self, err: _SysExcInfoType, test: TestCase) -> str:
        """Converts a sys.exc_info()-style tuple of values into a string."""
        exctype, value, tb = err
        # Skip test runner traceback levels
        while tb and self._is_relevant_tb_level(tb):  # type: ignore [attr-defined]
            tb = tb.tb_next

        msgLines = []
        if exctype is not None:
            # assert value is not None
            # assert tb is not None
            extract = Traceback.extract(exctype, value, tb, show_locals=True)
            tb_e = Traceback(extract, suppress=[unittest, testcases])
            with self.console.capture() as capture:
                self.console.print(tb_e)
            msgLines.append(capture.get())

        if self.buffer:
            assert isinstance(sys.stdout, io.StringIO)
            output = sys.stdout.getvalue()
            assert isinstance(sys.stderr, io.StringIO)
            error = sys.stderr.getvalue()
            if output:
                if not output.endswith("\n"):
                    output += "\n"
                msgLines.append(STDOUT_LINE % output)
            if error:
                if not error.endswith("\n"):
                    error += "\n"
                msgLines.append(STDERR_LINE % error)

        return "".join(msgLines)


class RichDebugSQLTextTestResult(DebugSQLTextTestResult, RichTextTestResult):
    def printErrorList(
        self,
        flavour: str,
        errors: list[tuple[TestCase, str], str],
    ) -> None:
        for test, err, sql_debug in errors:
            rule = Rule(style=DJANGO_GREEN)
            title = f"{flavour}: {self.getDescription(test)}"
            self.console.print(rule, title, rule)
            self.console.print("%s\n" % err)
            self.console.print(rule)
            self.console.print(sql_debug)


if django.VERSION >= (3, 0):

    class RichPDBDebugResult(PDBDebugResult, RichTextTestResult):
        pass


class RichTestRunner(DiscoverRunner.test_runner):
    resultclass = RichTextTestResult


class RichRunner(DiscoverRunner):
    test_runner = RichTestRunner

    def get_resultclass(self) -> type[RichTextTestResult] | None:
        if self.debug_sql:
            return RichDebugSQLTextTestResult
        elif django.VERSION >= (3, 0) and self.pdb:
            return RichPDBDebugResult
        return None
