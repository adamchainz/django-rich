from __future__ import annotations

import io
import sys
import time
import unittest
from types import TracebackType
from typing import Any, Iterable, TextIO, Tuple, Type, Union
from unittest.case import TestCase
from unittest.result import STDERR_LINE, STDOUT_LINE, failfast

from django.test import testcases
from django.test.runner import (  # type: ignore [attr-defined]
    DebugSQLTextTestResult,
    DiscoverRunner,
    PDBDebugResult,
)
from django.test.utils import TimeKeeper  # type: ignore [attr-defined]
from rich.color import Color
from rich.console import Console
from rich.rule import Rule
from rich.style import Style
from rich.traceback import Traceback

_SysExcInfoType = Union[
    Tuple[Type[BaseException], BaseException, TracebackType],
    Tuple[Type[BaseException], BaseException, None],
    Tuple[None, None, None],
]

DJANGO_GREEN = Style(color=Color.from_rgb(32, 170, 118))
DJANGO_GREEN_RULE = Rule(style=DJANGO_GREEN)
RED = Style(color="red")
YELLOW = Style(color="yellow")


class RichTextTestResult(unittest.TextTestResult):
    # Declaring attribute since typeshed had wrong capitalization
    # https://github.com/python/typeshed/pull/7340
    showAll: bool

    def __init__(
        self,
        stream: TextIO,
        descriptions: bool,
        verbosity: int,
    ) -> None:
        super().__init__(stream, descriptions, verbosity)
        self.console = Console(
            # Get underlying stream from _WritelnDecorator, normally sys.stderr:
            file=self.stream.stream,  # type: ignore [attr-defined]
        )
        self.collectedDurations: list[tuple[TestCase, float]] = []

    def startTest(self, test: TestCase) -> None:
        self._timing_start = time.perf_counter_ns()

    def stopTest(self, test: TestCase) -> None:
        total = (time.perf_counter_ns() - self._timing_start) / 1e9
        self.collectedDurations.append((test, total))

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
            self.console.print("ERROR", style=RED)
        elif self.dots:
            self.console.print("E", style=RED, end="")

    @failfast
    def addFailure(self, test: TestCase, err: _SysExcInfoType) -> None:
        self.failures.append((test, self._exc_info_to_string(err, test)))
        self._mirrorOutput = True
        if self.showAll:
            self.console.print("FAIL", style=RED)
        elif self.dots:
            self.console.print("F", style=RED, end="")

    def addSkip(self, test: TestCase, reason: str) -> None:
        self.skipped.append((test, reason))
        if self.showAll:
            self.console.print(f"skipped {reason!r}", style=YELLOW)
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
            self.stream.write("%s\n" % err)

    def _exc_info_to_string(self, err: _SysExcInfoType, test: TestCase) -> str:
        """Converts a sys.exc_info()-style tuple of values into a string."""
        exctype, value, tb = err
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
            self.stream.write("%s\n" % err)
            self.console.print(DJANGO_GREEN_RULE)
            self.console.print(sql_debug)


class RichPDBDebugResult(PDBDebugResult, RichTextTestResult):  # type: ignore [misc]
    pass


class RichTestRunner(DiscoverRunner.test_runner):  # type: ignore [misc]
    resultclass = RichTextTestResult


class RichRunner(DiscoverRunner):
    pdb: bool  # django-stubs missing

    test_runner = RichTestRunner

    # django-stubs bad return type, fixed in:
    # https://github.com/typeddjango/django-stubs/pull/1069
    def get_resultclass(  # type: ignore [override]
        self,
    ) -> type[unittest.TextTestResult] | None:
        if self.debug_sql:
            return RichDebugSQLTextTestResult
        elif self.pdb:
            return RichPDBDebugResult
        return None

    def suite_result(  # type: ignore [override]
        self,
        suite: unittest.TestSuite,
        result: RichTextTestResult,
        **kwargs: Any,
    ) -> int:
        time_keeper = self.time_keeper  # type: ignore [attr-defined]
        if result.collectedDurations and isinstance(time_keeper, TimeKeeper):
            max_to_print = 100 if self.verbosity > 1 else 10
            amount_to_print = min(len(result.collectedDurations), max_to_print)
            result.console.print(
                DJANGO_GREEN_RULE,
                f"Slowest {amount_to_print} Tests",
                DJANGO_GREEN_RULE,
            )
            by_time = sorted(
                result.collectedDurations, key=lambda x: x[1], reverse=True
            )
            by_time = by_time[:amount_to_print]
            for func_name, timing in by_time:
                result.console.print(
                    f"[bold yellow]{float(timing):.3f}s[/bold yellow] {func_name}"
                )
        return len(result.failures) + len(result.errors)
