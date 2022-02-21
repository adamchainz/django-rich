from __future__ import annotations

import sys
import unittest
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


class RichMixin(unittest.TestResult):
    console = Console(stderr=True)
    django_green = Style(color=Color.from_rgb(32, 170, 118))

    @failfast
    def addError(self, test, err):
        self.errors.append((test, self._exc_info_to_string(err, test)))
        self._mirrorOutput = True
        if self.showAll:
            self.console.print("ERROR", style=Style(color="red"))
        elif self.dots:
            self.console.print("E", style=Style(color="red"), end="")

    def addSuccess(self, test):
        if self.showAll:
            self.console.print("ok", style=self.django_green)
        elif self.dots:
            self.console.print(".", style=self.django_green, end="")

    @failfast
    def addFailure(self, test, err):
        self.failures.append((test, self._exc_info_to_string(err, test)))
        self._mirrorOutput = True
        if self.showAll:
            self.console.print("FAIL", style=Style(color="red"))
        elif self.dots:
            self.console.print("F", style=Style(color="red"), end="")

    def addSkip(self, test, reason):
        self.skipped.append((test, reason))
        if self.showAll:
            self.console.print(f"skipped {reason!r}", style=Style(color="yellow"))
        elif self.dots:
            self.console.print("s", style=Style(color="yellow"), end="")

    def addExpectedFailure(self, test, err):
        self.expectedFailures.append((test, self._exc_info_to_string(err, test)))
        if self.showAll:
            self.console.print("expected failure", style=Style(color="yellow"))
        elif self.dots:
            self.console.print("x", style=Style(color="yellow"), end="")

    @failfast
    def addUnexpectedSuccess(self, test):
        self.unexpectedSuccesses.append(test)
        if self.showAll:
            self.console.print("unexpected success", style=Style(color="red"))
        elif self.dots:
            self.console.print("u", style=Style(color="red"), end="")

    def _exc_info_to_string(self, err, test):
        """Converts a sys.exc_info()-style tuple of values into a string."""
        exctype, value, tb = err
        # Skip test runner traceback levels
        while tb and self._is_relevant_tb_level(tb):
            tb = tb.tb_next

        extract = Traceback.extract(exctype, value, tb, show_locals=True)
        tb_e = Traceback(extract, suppress=[unittest, testcases])
        with self.console.capture() as capture:
            self.console.print(tb_e)
        msgLines = capture.get()
        if self.buffer:
            output = sys.stdout.getvalue()
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

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            r = Rule(style=self.django_green)
            title = f"{flavour}: {self.getDescription(test)}"
            self.console.print(r, title, r)
            self.stream.writeln("%s" % err)


class RichTextTestResult(RichMixin, unittest.TextTestResult):
    pass


class RichDebugSQLTextTestResult(RichMixin, DebugSQLTextTestResult):
    pass


if django.VERSION >= (3, 0):

    class RichPDBDebugResult(RichMixin, PDBDebugResult):
        pass


class RichTestRunner(DiscoverRunner.test_runner):
    resultclass = RichTextTestResult


class RichRunner(DiscoverRunner):
    test_runner = RichTestRunner

    def get_resultclass(self):
        if self.debug_sql:
            return RichDebugSQLTextTestResult
        elif django.VERSION >= (3, 0) and self.pdb:
            return RichPDBDebugResult
