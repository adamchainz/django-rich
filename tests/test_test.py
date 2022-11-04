from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest.case
from pathlib import Path

import django
import pytest
from django.db import connection
from django.test import SimpleTestCase
from django.test import TestCase


@pytest.mark.skip(reason="Run below via Django unittest subprocess.")
class ExampleTests(TestCase):
    def test_pass(self):
        self.assertEqual(1, 1)

    def test_error(self):
        raise ValueError("Woops")

    def test_failure(self):
        self.assertEqual(1, 2)

    def test_failure_django_assertion(self):
        # django-stubs doesn't know about assertURLEqual until:
        # https://github.com/typeddjango/django-stubs/pull/1102
        self.assertURLEqual("/url/", "/test/")  # type: ignore [attr-defined]

    def test_failure_sql_query(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1234, %s",
                (5678,),
            )
        self.assertTrue(False)

    @unittest.skip("some reason")
    def test_skip(self):  # pragma: no cover
        raise ValueError("never run")

    @unittest.expectedFailure
    def test_expected_failure(self):
        self.assertEqual(1, 2)

    @unittest.expectedFailure
    def test_unexpected_success(self):
        self.assertEqual(1, 1)

    def test_pass_output(self):
        print("This is some example output")
        print("This is some example output", file=sys.stderr)

    def test_failure_stdout(self):
        print("This is some example output")
        self.assertTrue(False)

    def test_failure_stdout_no_newline(self):
        print("This is some example output", end="")
        self.assertTrue(False)

    def test_failure_stderr(self):
        print("This is some example output", file=sys.stderr)
        self.assertTrue(False)

    def test_failure_stderr_no_newline(self):
        print("This is some example output", end="", file=sys.stderr)
        self.assertTrue(False)


SETUP_CFG_PATH = Path(__file__).resolve().parent.parent / "setup.cfg"


class TestRunnerTests(SimpleTestCase):
    def run_test(
        self, *args: str, input: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python",
                "-m",
                "django",
                "test",
                *args,
            ],
            input=input,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "DJANGO_SETTINGS_MODULE": "tests.settings",
                "COVERAGE_PROCESS_START": str(SETUP_CFG_PATH),
            },
        )

    def test_does_not_exist(self):
        result = self.run_test("does_not_exist")
        assert result.returncode == 1
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[:6] == [
                "E",
                "─" * 80,
                "ERROR: does_not_exist (unittest.loader._FailedTest.does_not_exist)",
                "─" * 80,
                "ImportError: Failed to import test module: does_not_exist",
                "Traceback (most recent call last):",
            ]
        else:
            assert lines[:6] == [
                "E",
                "─" * 80,
                "ERROR: does_not_exist (unittest.loader._FailedTest)",
                "─" * 80,
                "ImportError: Failed to import test module: does_not_exist",
                "Traceback (most recent call last):",
            ]

    def test_pass_quiet(self):
        result = self.run_test("-v", "0", f"{__name__}.ExampleTests.test_pass")
        assert result.returncode == 0
        assert result.stderr.splitlines()[:1] == [
            "-" * 70,
        ]

    def test_pass_normal(self):
        result = self.run_test(f"{__name__}.ExampleTests.test_pass")
        assert result.returncode == 0
        assert result.stderr.splitlines()[1:3] == [
            ".",
            "-" * 70,
        ]

    def test_pass_verbose(self):
        result = self.run_test("-v", "2", f"{__name__}.ExampleTests.test_pass")
        assert result.returncode == 0
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[1:4] == [
                "test_pass (tests.test_test.ExampleTests.test_pass) ... ok",
                "",
                "-" * 70,
            ]
        else:
            assert lines[1:4] == [
                "test_pass (tests.test_test.ExampleTests) ... ok",
                "",
                "-" * 70,
            ]

    def test_error_quiet(self):
        result = self.run_test("-v", "0", f"{__name__}.ExampleTests.test_error")
        assert result.returncode == 1
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[:2] == [
                "─" * 80,
                "ERROR: test_error (tests.test_test.ExampleTests.test_error)",
            ]
        else:
            assert lines[:2] == [
                "─" * 80,
                "ERROR: test_error (tests.test_test.ExampleTests)",
            ]
        assert "─ locals ─" in result.stderr

    def test_error_normal(self):
        result = self.run_test(f"{__name__}.ExampleTests.test_error")
        assert result.returncode == 1
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[1:4] == [
                "E",
                "─" * 80,
                "ERROR: test_error (tests.test_test.ExampleTests.test_error)",
            ]
        else:
            assert lines[1:4] == [
                "E",
                "─" * 80,
                "ERROR: test_error (tests.test_test.ExampleTests)",
            ]
        assert "─ locals ─" in result.stderr

    def test_error_verbose(self):
        result = self.run_test("-v", "2", f"{__name__}.ExampleTests.test_error")
        assert result.returncode == 1
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[1:5] == [
                "test_error (tests.test_test.ExampleTests.test_error) ... ERROR",
                "",
                "─" * 80,
                "ERROR: test_error (tests.test_test.ExampleTests.test_error)",
            ]
        else:
            assert lines[1:5] == [
                "test_error (tests.test_test.ExampleTests) ... ERROR",
                "",
                "─" * 80,
                "ERROR: test_error (tests.test_test.ExampleTests)",
            ]
        assert "─ locals ─" in result.stderr

    def test_failure_quiet(self):
        result = self.run_test("-v", "0", f"{__name__}.ExampleTests.test_failure")
        assert result.returncode == 1
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[:2] == [
                "─" * 80,
                "FAIL: test_failure (tests.test_test.ExampleTests.test_failure)",
            ]
        else:
            assert lines[:2] == [
                "─" * 80,
                "FAIL: test_failure (tests.test_test.ExampleTests)",
            ]
        assert "─ locals ─" in result.stderr

    def test_failure_normal(self):
        result = self.run_test(f"{__name__}.ExampleTests.test_failure")
        assert result.returncode == 1
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[1:4] == [
                "F",
                "─" * 80,
                "FAIL: test_failure (tests.test_test.ExampleTests.test_failure)",
            ]
        else:
            assert lines[1:4] == [
                "F",
                "─" * 80,
                "FAIL: test_failure (tests.test_test.ExampleTests)",
            ]
        assert "─ locals ─" in result.stderr

    def test_failure_verbose(self):
        result = self.run_test("-v", "2", f"{__name__}.ExampleTests.test_failure")
        assert result.returncode == 1
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[1:5] == [
                "test_failure (tests.test_test.ExampleTests.test_failure) ... FAIL",
                "",
                "─" * 80,
                "FAIL: test_failure (tests.test_test.ExampleTests.test_failure)",
            ]
        else:
            assert lines[1:5] == [
                "test_failure (tests.test_test.ExampleTests) ... FAIL",
                "",
                "─" * 80,
                "FAIL: test_failure (tests.test_test.ExampleTests)",
            ]
        assert "─ locals ─" in result.stderr

    def test_skip_quiet(self):
        result = self.run_test("-v", "0", f"{__name__}.ExampleTests.test_skip")
        assert result.returncode == 0
        assert result.stderr.splitlines()[:1] == [
            "-" * 70,
        ]

    def test_skip_normal(self):
        result = self.run_test(f"{__name__}.ExampleTests.test_skip")
        assert result.returncode == 0
        assert result.stderr.splitlines()[1:3] == [
            "s",
            "-" * 70,
        ]

    def test_skip_verbose(self):
        result = self.run_test("-v", "2", f"{__name__}.ExampleTests.test_skip")
        assert result.returncode == 0
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[1:4] == [
                (
                    "test_skip (tests.test_test.ExampleTests.test_skip) ... "
                    + "skipped 'some reason'"
                ),
                "",
                "-" * 70,
            ]
        else:
            assert lines[1:4] == [
                "test_skip (tests.test_test.ExampleTests) ... skipped 'some reason'",
                "",
                "-" * 70,
            ]

    def test_expected_failure_quiet(self):
        result = self.run_test(
            "-v", "0", f"{__name__}.ExampleTests.test_expected_failure"
        )
        assert result.returncode == 0
        assert result.stderr.splitlines()[:1] == [
            "-" * 70,
        ]

    def test_expected_failure_normal(self):
        result = self.run_test(f"{__name__}.ExampleTests.test_expected_failure")
        assert result.returncode == 0
        assert result.stderr.splitlines()[1:3] == [
            "x",
            "-" * 70,
        ]

    def test_expected_failure_verbose(self):
        result = self.run_test(
            "-v", "2", f"{__name__}.ExampleTests.test_expected_failure"
        )
        assert result.returncode == 0
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[1:4] == [
                (
                    "test_expected_failure (tests.test_test.ExampleTests."
                    + "test_expected_failure) ... expected failure"
                ),
                "",
                "-" * 70,
            ]
        else:
            assert lines[1:4] == [
                (
                    "test_expected_failure (tests.test_test.ExampleTests) ... "
                    + "expected failure"
                ),
                "",
                "-" * 70,
            ]

    def test_unexpected_success_quiet(self):
        result = self.run_test(
            "-v", "0", f"{__name__}.ExampleTests.test_unexpected_success"
        )

        if django.VERSION >= (4, 1):
            assert result.returncode == 1
        else:
            assert result.returncode == 0
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[:1] == ["=" * 70]
        else:
            assert lines[:1] == ["-" * 70]

    def test_unexpected_success_normal(self):
        result = self.run_test(f"{__name__}.ExampleTests.test_unexpected_success")

        if django.VERSION >= (4, 1):
            assert result.returncode == 1
        else:
            assert result.returncode == 0
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[1:3] == [
                "u",
                "=" * 70,
            ]
        else:
            assert lines[1:3] == [
                "u",
                "-" * 70,
            ]

    def test_unexpected_success_verbose(self):
        result = self.run_test(
            "-v", "2", f"{__name__}.ExampleTests.test_unexpected_success"
        )
        if django.VERSION >= (4, 1):
            assert result.returncode == 1
        else:
            assert result.returncode == 0
        lines = result.stderr.splitlines()
        if sys.version_info >= (3, 11):
            assert lines[1:4] == [
                (
                    "test_unexpected_success (tests.test_test.ExampleTests."
                    + "test_unexpected_success) ... unexpected success"
                ),
                "",
                "=" * 70,
            ]
        else:
            assert lines[1:4] == [
                (
                    "test_unexpected_success (tests.test_test.ExampleTests) "
                    + "... unexpected success"
                ),
                "",
                "-" * 70,
            ]

    def test_debug_sql(self):
        result = self.run_test(
            "--debug-sql", f"{__name__}.ExampleTests.test_failure_sql_query"
        )

        assert result.returncode == 1
        lines = result.stderr.splitlines()
        assert "─ locals ─" in result.stderr
        assert lines[-10:-7] == [
            "AssertionError: False is not true",
            "",
            "─" * 80,
        ]
        if django.VERSION >= (4, 0):
            # https://docs.djangoproject.com/en/4.0/releases/4.0/#logging
            sql_line_re = (
                r"\(\d.\d\d\d\) SELECT 1234, 5678; args=\(5678,\); alias=default"
            )
        else:
            sql_line_re = r"\(\d.\d\d\d\) SELECT 1234, 5678; args=\(5678,\)"
        assert re.match(sql_line_re, lines[-7])
        assert lines[-6:-4] == [
            "",
            "-" * 70,
        ]

    def test_pdb(self):
        result = self.run_test(
            "--pdb",
            f"{__name__}.ExampleTests.test_failure",
            input="p 2 * 2\n",
        )

        assert result.returncode == 1
        lines = result.stdout.splitlines()
        expected = [
            "System check identified no issues (0 silenced).",
            "",
            "Opening PDB: AssertionError('1 != 2')",
        ]
        if django.VERSION >= (4,):
            expected.insert(0, "Found 1 test(s).")
        assert lines[: len(expected)] == expected

        assert lines[len(expected) + 1 : len(expected) + 4] == [
            "-> raise self.failureException(msg)",
            "(Pdb) 4",
            "(Pdb) ",
        ]

    def test_failure_django_assertion(self):
        "Django and Unit test modules are hidden in tracebacks."
        result = self.run_test(f"{__name__}.ExampleTests.test_failure_django_assertion")
        assert result.returncode == 1
        assert "testPartExecutor" not in result.stderr
        assert "_callTestMethod" not in result.stderr
        assert 'self.assertURLEqual("/url/", "/test/")' in result.stderr
        assert 'self.assertURLEqual("/url/", "/test/")' in result.stderr
        assert result.stderr.count("─ locals ─") == 1

    def test_buffer_pass(self):
        result = self.run_test("--buffer", f"{__name__}.ExampleTests.test_pass_output")
        assert result.returncode == 0
        assert "This is some example output" not in result.stdout
        assert "This is some example output" not in result.stderr

    def test_buffer_stdout(self):
        result = self.run_test(
            "--buffer", f"{__name__}.ExampleTests.test_failure_stdout"
        )
        assert result.returncode == 1
        assert result.stderr.splitlines()[-10:-4] == [
            "AssertionError: False is not true",
            "",
            "Stdout:",
            "This is some example output",
            "",
            "-" * 70,
        ]

    def test_buffer_stdout_no_newline(self):
        result = self.run_test(
            "--buffer", f"{__name__}.ExampleTests.test_failure_stdout_no_newline"
        )
        assert result.returncode == 1
        assert result.stderr.splitlines()[-10:-4] == [
            "AssertionError: False is not true",
            "",
            "Stdout:",
            "This is some example output",
            "",
            "-" * 70,
        ]

    def test_buffer_stderr(self):
        result = self.run_test(
            "--buffer", f"{__name__}.ExampleTests.test_failure_stderr"
        )
        assert result.returncode == 1
        assert result.stderr.splitlines()[-10:-4] == [
            "AssertionError: False is not true",
            "",
            "Stderr:",
            "This is some example output",
            "",
            "-" * 70,
        ]

    def test_buffer_stderr_no_newline(self):
        result = self.run_test(
            "--buffer", f"{__name__}.ExampleTests.test_failure_stderr_no_newline"
        )
        assert result.returncode == 1
        assert result.stderr.splitlines()[-10:-4] == [
            "AssertionError: False is not true",
            "",
            "Stderr:",
            "This is some example output",
            "",
            "-" * 70,
        ]
