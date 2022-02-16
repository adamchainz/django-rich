from __future__ import annotations

import sys
import unittest
from unittest.result import STDERR_LINE, STDOUT_LINE

from django.test import testcases
from django.test.runner import DebugSQLTextTestResult, DiscoverRunner, PDBDebugResult
from rich.color import Color
from rich.console import Console
from rich.rule import Rule
from rich.style import Style
from rich.traceback import Traceback


class RichMixin(unittest.TextTestResult):
    # Traceback width defaults to 100
    console = Console(width=100, stderr=True)
    django_green = Style(color=Color.from_rgb(32, 170, 118))

    def addError(self, test, err):
        super(unittest.TextTestResult, self).addError(test, err)
        if self.showAll:
            self.console.print("ERROR", style=Style(color="red"))
        elif self.dots:
            self.console.print("E", style=Style(color="red"), end="")

    def addSuccess(self, test):
        super(unittest.TextTestResult, self).addSuccess(test)
        if self.showAll:
            self.console.print("ok", style=self.django_green)
        elif self.dots:
            self.console.print(".", style=self.django_green, end="")

    def addFailure(self, test, err):
        super(unittest.TextTestResult, self).addFailure(test, err)
        if self.showAll:
            self.console.print("FAIL", style=Style(color="red"))
        elif self.dots:
            self.console.print("F", style=Style(color="red"), end="")

    def addSkip(self, test, reason):
        super(unittest.TextTestResult, self).addSkip(test, reason)
        if self.showAll:
            self.console.print(
                "skipped {0!r}".format(reason), style=Style(color="yellow")
            )
        elif self.dots:
            self.console.print("s", style=Style(color="yellow"), end="")

    def addExpectedFailure(self, test, err):
        super(unittest.TextTestResult, self).addExpectedFailure(test, err)
        if self.showAll:
            self.console.print("expected failure", style=Style(color="yellow"))
        elif self.dots:
            self.console.print("x", style=Style(color="yellow"), end="")

    def addUnexpectedSuccess(self, test):
        super(unittest.TextTestResult, self).addUnexpectedSuccess(test)
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


class RichPDBDebugResult(RichMixin, PDBDebugResult):
    pass


class RichTestRunner(unittest.TextTestRunner):
    resultclass = RichTextTestResult


class RichDiscoverRunner(DiscoverRunner):
    test_runner = RichTestRunner

    def get_resultclass(self):
        if self.debug_sql:
            return RichDebugSQLTextTestResult
        elif self.pdb:
            return RichPDBDebugResult
