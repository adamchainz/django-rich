from __future__ import annotations

import io
import sys
import unittest
from collections.abc import Iterable
from types import TracebackType
from typing import Any, Union, cast
from unittest.case import (  # type: ignore [attr-defined]
    TestCase,
    _SubTest,
)
from unittest.result import STDERR_LINE, STDOUT_LINE, TestResult, failfast
from unittest.runner import _WritelnDecorator

from django.test import testcases
from django.test.runner import DebugSQLTextTestResult, DiscoverRunner, PDBDebugResult
from rich.color import Color
from rich.console import Console
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.traceback import Traceback

_SysExcInfoType = Union[
    tuple[type[BaseException], BaseException, TracebackType],
    tuple[None, None, None],
]

DJANGO_GREEN = Style(color=Color.from_rgb(32, 170, 118))
DJANGO_GREEN_RULE = Rule(style=DJANGO_GREEN)
RED = Style(color="red")
YELLOW = Style(color="yellow")


class RichTextTestResult(unittest.TextTestResult):
    # Declaring attribute as _newline was added in Python 3.11.
    _newline: bool

    def __init__(
        self,
        stream: _WritelnDecorator,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(stream, *args, **kwargs)
        self.console = Console(
            # Get underlying stream from _WritelnDecorator, normally sys.stderr:
            file=self.stream.stream,
        )
        with self.console.capture() as cap:
            self.console.print(Rule(characters="═", style=DJANGO_GREEN))
        self.separator1 = cap.get().rstrip("\n")
        with self.console.capture() as cap:
            self.console.print(Rule(characters="━", style=DJANGO_GREEN))
        self.separator2 = cap.get().rstrip("\n")
        if sys.version_info < (3, 11):
            self._newline = True

    def startTest(self, test: TestCase) -> None:
        super().startTest(test)
        if sys.version_info < (3, 11):
            self._newline = False

    def addSuccess(self, test: TestCase) -> None:
        if self.showAll:
            self._write_status(test, "ok")
        elif self.dots:
            self.console.print(".", style=DJANGO_GREEN, end="")

    @failfast
    def addError(self, test: TestCase, err: _SysExcInfoType) -> None:
        self.errors.append((test, self._exc_info_to_string(err, test)))
        self._mirrorOutput = True
        if self.showAll:
            self._write_status(test, "ERROR")
        elif self.dots:
            self.console.print("E", style=RED, end="")

    @failfast
    def addFailure(self, test: TestCase, err: _SysExcInfoType) -> None:
        self.failures.append((test, self._exc_info_to_string(err, test)))
        self._mirrorOutput = True
        if self.showAll:
            self._write_status(test, "FAIL")
        elif self.dots:
            self.console.print("F", style=RED, end="")

    def addSkip(self, test: TestCase, reason: str) -> None:
        self.skipped.append((test, reason))
        if self.showAll:
            self._write_status(test, f"skipped {reason!r}")
        elif self.dots:
            self.console.print("s", style=YELLOW, end="")

    def addExpectedFailure(self, test: TestCase, err: _SysExcInfoType) -> None:
        self.expectedFailures.append((test, self._exc_info_to_string(err, test)))
        if self.showAll:
            self.console.print("expected failure", style=YELLOW)
        elif self.dots:
            self.console.print("x", style=YELLOW, end="")

    @failfast
    def addUnexpectedSuccess(self, test: TestCase) -> None:
        self.unexpectedSuccesses.append(test)
        if self.showAll:
            self.console.print("unexpected success", style=RED)
        elif self.dots:
            self.console.print("u", style=RED, end="")

    def printErrorList(
        self,
        flavour: str,
        errors: Iterable[tuple[TestCase, str]],
    ) -> None:
        for test, err in errors:
            title = f"{flavour}: {self.getDescription(test)}"
            self.console.print(DJANGO_GREEN_RULE, title, DJANGO_GREEN_RULE)
            self.stream.write(f"{err}\n")

    def _write_status(self, test: TestCase, status: str) -> None:
        is_subtest = isinstance(test, _SubTest)
        if is_subtest or self._newline:
            if not self._newline:
                self.console.print("\n", end="")
            if is_subtest:
                self.console.print("  ", end="")
            self.console.print(self.getDescription(test), end="")
            self.console.print(" ... ", end="")
        if status == "FAIL":
            self.console.print("FAIL", style=RED)
        elif status == "ERROR":
            self.console.print("ERROR", style=RED)
        elif status.startswith("skipped"):
            self.console.print(status, style=YELLOW)
        else:
            self.console.print(status, style=DJANGO_GREEN)
        self._newline = True

    def addSubTest(
        self, test: TestCase, subtest: TestCase, err: _SysExcInfoType | None
    ) -> None:
        if err is not None:
            if self.showAll:
                if issubclass(err[0], subtest.failureException):  # type: ignore [arg-type]
                    self._write_status(subtest, "FAIL")
                else:
                    self._write_status(subtest, "ERROR")
            elif self.dots:
                if issubclass(err[0], subtest.failureException):  # type: ignore [arg-type]
                    self.console.print("F", style=RED, end="")
                else:
                    self.console.print("E", style=RED, end="")
        TestResult.addSubTest(self, test, subtest, err)

    def _exc_info_to_string(self, err: _SysExcInfoType, test: TestCase) -> str:
        """Converts a sys.exc_info()-style tuple of values into a string."""
        exctype, value, tb = err

        if hasattr(self, "_clean_tracebacks"):
            # Post-bpo-24959 - merged to Python 3.11, backported to 3.9 and 3.10
            tb = self._clean_tracebacks(exctype, value, tb, test)
        else:  # pragma: no cover
            # needed on old 3.9 and 3.10 patch versions, but not testing those
            # Skip test runner traceback levels
            while tb and self._is_relevant_tb_level(tb):  # type: ignore [attr-defined]
                tb = tb.tb_next

        msgLines = []
        if exctype is not None:  # pragma: no branch  # can't work when this isn't true
            assert value is not None
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
    # DebugSQLTextTestResult adds sql_debug to errors in type-incompatible way
    def printErrorList(  # type: ignore [override]
        self,
        flavour: str,
        errors: Iterable[tuple[TestCase, str, str]],
    ) -> None:
        for test, err, sql_debug in errors:
            title = f"{flavour}: {self.getDescription(test)}"
            self.console.print(DJANGO_GREEN_RULE, title, DJANGO_GREEN_RULE)
            self.stream.write(f"{err}\n")
            self.console.print(DJANGO_GREEN_RULE)
            self.console.print(sql_debug)


class RichPDBDebugResult(PDBDebugResult, RichTextTestResult):
    pass


class RichTestRunner(unittest.TextTestRunner):
    # Ignoring typing issue because it’s hard to make RichTextTestResult match
    # the types of TextTestResult.
    resultclass = RichTextTestResult  # type: ignore [assignment]

    def _printDurations(self, result: RichTextTestResult) -> None:
        if not result.collectedDurations:
            return
        ls = sorted(result.collectedDurations, key=lambda x: x[1], reverse=True)
        if cast(int, self.durations) > 0:  # typeshed has a bad hint (?!)
            ls = ls[: cast(int, self.durations)]

        table = Table(title="Slowest test durations", title_style=YELLOW)
        table.add_column("Duration", justify="right", no_wrap=True)
        table.add_column("Test")

        hidden = False
        for test, elapsed in ls:
            if self.verbosity < 2 and elapsed < 0.001:
                hidden = True
                continue
            table.add_row(f"{elapsed:.3f}s", test)
        if hidden:
            table.caption = (
                "Durations < 0.001s were hidden. Use -v to show these durations."
            )

        if table.rows:
            result.console.print(table)
        else:
            result.console.print(table.title, style=table.title_style)
            result.console.print(table.caption, style="table.caption", highlight=False)


class RichRunner(DiscoverRunner):
    test_runner = RichTestRunner

    def get_resultclass(self) -> type[unittest.TextTestResult] | None:
        if self.debug_sql:
            return RichDebugSQLTextTestResult
        elif self.pdb:
            return RichPDBDebugResult
        return None
