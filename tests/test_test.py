from __future__ import annotations

import os
import subprocess
import unittest
import unittest.case
from pathlib import Path

import django
import pytest
from django.db import connection
from django.test import SimpleTestCase, TestCase


@pytest.mark.skip(reason="Run below via Django unittest subprocess.")
class ExampleTests(TestCase):
    def test_pass(self):
        self.assertEqual(1, 1)

    def test_error(self):
        raise ValueError("Woops")

    def test_failure(self):
        self.assertEqual(1, 2)

    def test_failure_django_assertion(self):
        self.assertURLEqual("/url/", "/test/")

    def test_failure_sql_query(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1234")
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


SETUP_CFG_PATH = Path(__file__).resolve().parent.parent / "setup.cfg"


class TestRunnerTests(SimpleTestCase):
    def run_test(self, *args, **kwargs):
        return subprocess.run(
            [
                "python",
                "-m",
                "django",
                "test",
                *args,
            ],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "DJANGO_SETTINGS_MODULE": "tests.settings",
                "COVERAGE_PROCESS_START": str(SETUP_CFG_PATH),
            },
            **kwargs,
        )

    def test_does_not_exist(self):
        result = self.run_test("does_not_exist")
        assert result.returncode == 1
        assert result.stderr.splitlines()[:6] == [
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
        assert result.stderr.splitlines()[1:4] == [
            "test_pass (tests.test_test.ExampleTests) ... ok",
            "",
            "-" * 70,
        ]

    def test_error_quiet(self):
        result = self.run_test("-v", "0", f"{__name__}.ExampleTests.test_error")
        assert result.returncode == 1
        assert result.stderr.splitlines()[:2] == [
            "─" * 80,
            "ERROR: test_error (tests.test_test.ExampleTests)",
        ]
        assert "─ locals ─" in result.stderr

    def test_error_normal(self):
        result = self.run_test(f"{__name__}.ExampleTests.test_error")
        assert result.returncode == 1
        assert result.stderr.splitlines()[1:4] == [
            "E",
            "─" * 80,
            "ERROR: test_error (tests.test_test.ExampleTests)",
        ]
        assert "─ locals ─" in result.stderr

    def test_error_verbose(self):
        result = self.run_test("-v", "2", f"{__name__}.ExampleTests.test_error")
        assert result.returncode == 1
        assert result.stderr.splitlines()[1:5] == [
            "test_error (tests.test_test.ExampleTests) ... ERROR",
            "",
            "─" * 80,
            "ERROR: test_error (tests.test_test.ExampleTests)",
        ]
        assert "─ locals ─" in result.stderr

    def test_failure_quiet(self):
        result = self.run_test("-v", "0", f"{__name__}.ExampleTests.test_failure")
        assert result.returncode == 1
        assert result.stderr.splitlines()[:2] == [
            "─" * 80,
            "FAIL: test_failure (tests.test_test.ExampleTests)",
        ]
        assert "─ locals ─" in result.stderr

    def test_failure_normal(self):
        result = self.run_test(f"{__name__}.ExampleTests.test_failure")
        assert result.returncode == 1
        assert result.stderr.splitlines()[1:4] == [
            "F",
            "─" * 80,
            "FAIL: test_failure (tests.test_test.ExampleTests)",
        ]
        assert "─ locals ─" in result.stderr

    def test_failure_verbose(self):
        result = self.run_test("-v", "2", f"{__name__}.ExampleTests.test_failure")
        assert result.returncode == 1
        assert result.stderr.splitlines()[1:5] == [
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
        assert result.stderr.splitlines()[1:4] == [
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
        assert result.stderr.splitlines()[1:4] == [
            "test_expected_failure (tests.test_test.ExampleTests) ... expected failure",
            "",
            "-" * 70,
        ]

    def test_unexpected_success_quiet(self):
        result = self.run_test(
            "-v", "0", f"{__name__}.ExampleTests.test_unexpected_success"
        )
        assert result.returncode == 0
        assert result.stderr.splitlines()[:1] == [
            "-" * 70,
        ]

    def test_unexpected_success_normal(self):
        result = self.run_test(f"{__name__}.ExampleTests.test_unexpected_success")
        assert result.returncode == 0
        assert result.stderr.splitlines()[1:3] == [
            "u",
            "-" * 70,
        ]

    def test_unexpected_success_verbose(self):
        result = self.run_test(
            "-v", "2", f"{__name__}.ExampleTests.test_unexpected_success"
        )
        assert result.returncode == 0
        assert result.stderr.splitlines()[1:4] == [
            (
                "test_unexpected_success (tests.test_test.ExampleTests) ... "
                + "unexpected success"
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
        assert lines[-10:-4] == [
            "AssertionError: False is not true",
            "",
            "─" * 80,
            "(0.000) SELECT 1234; args=None; alias=default",
            "",
            "-" * 70,
        ]

    @pytest.mark.skipif(django.VERSION < (3,), reason="--pdb added in Django 3.0")
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
