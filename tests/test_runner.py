from __future__ import annotations

import os
import subprocess
import unittest

import pytest
from django.test import SimpleTestCase


@pytest.mark.skip(reason="Run these unittest tests in a sub-process.")
class UnitTestRunnerTests(SimpleTestCase):
    def test_traceback(self):
        raise ValueError

    def test_assertion(self):
        self.assertEqual(1, 2)

    def test_django_assertion(self):
        "Tests can have descriptions."
        self.assertURLEqual("/url/", "/test/")

    def test_pass(self):
        self.assertEqual(1, 1)

    @unittest.skip("A skipped test.")
    def test_skip(self):
        raise ValueError

    @unittest.expectedFailure
    def test_expected_fail(self):
        self.assertEqual(1, 2)

    @unittest.expectedFailure
    def test_unexpected_success(self):
        self.assertEqual(1, 1)


class TestRunnerTests:
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "tests.settings",
    }

    def test_traceback(self):
        OUTPUT = "─ locals ─"

        stderr = subprocess.run(
            [
                "python",
                "-m",
                "django",
                "test",
                "tests.test_runner.UnitTestRunnerTests.test_traceback",
            ],
            capture_output=True,
            text=True,
            env=self.env,
        ).stderr
        assert OUTPUT in stderr

    def test_pdb_and_sql(self):
        OUTPUT = "─ locals ─"

        stderr = subprocess.run(
            [
                "python",
                "-m",
                "django",
                "test",
                "tests.test_runner.UnitTestRunnerTests.test_assertion",
            ],
            capture_output=True,
            text=True,
        ).stderr
        assert OUTPUT in stderr

        stderr = subprocess.run(
            [
                "python",
                "-m",
                "django",
                "test",
                "--pdb",
                "tests.test_runner.UnitTestRunnerTests.test_assertion",
            ],
            capture_output=True,
            text=True,
        ).stderr
        assert OUTPUT in stderr

        stderr = subprocess.run(
            [
                "python",
                "-m",
                "django",
                "test",
                "--debug-sql",
                "tests.test_runner.UnitTestRunnerTests.test_assertion",
            ],
            capture_output=True,
            text=True,
        ).stderr
        assert OUTPUT in stderr

    def test_django_assertion(sel):
        "Django and Unit test modules are hidden in traceback."
        OUTPUT = "─ Traceback (most recent call last) ─"

        stderr = subprocess.run(
            [
                "python",
                "-m",
                "django",
                "test",
                "tests.test_runner.UnitTestRunnerTests.test_django_assertion",
            ],
            capture_output=True,
            text=True,
        ).stderr
        assert stderr.count(OUTPUT) == 1
