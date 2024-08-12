from __future__ import annotations

import io
import sys
import unittest
from types import TracebackType
from typing import Any
from typing import Iterable
from typing import TextIO
from typing import Tuple
from typing import Type
from typing import Union
from typing import cast
from unittest.case import TestCase
from unittest.result import STDERR_LINE
from unittest.result import STDOUT_LINE
from unittest.result import failfast

from django.test import testcases
from django.test.runner import DebugSQLTextTestResult
from django.test.runner import DiscoverRunner
from django.test.runner import PDBDebugResult
from rich.color import Color
from rich.console import Console
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
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
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(stream, *args, **kwargs)
        self.console = Console(
            # Get underlying stream from _WritelnDecorator, normally sys.stderr:
            file=self.stream.stream,  # type: ignore [attr-defined]
        )
        with self.console.capture() as cap:
            self.console.print(Rule(characters="═", style=DJANGO_GREEN))
        self.separator1 = cap.get().rstrip("\n")
        with self.console.capture() as cap:
            self.console.print(Rule(characters="━", style=DJANGO_GREEN))
        self.separator2 = cap.get().rstrip("\n")

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


class RichPDBDebugResult(PDBDebugResult, RichTextTestResult):
    pass


class RichTestRunner(unittest.TextTestRunner):
    resultclass = RichTextTestResult

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
            table.add_row("%.3fs" % elapsed, test)
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
