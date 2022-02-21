from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

import django
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


SETUP_CFG_PATH = Path(__file__).resolve().parent.parent / "setup.cfg"


class TestRunnerTests(SimpleTestCase):
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "tests.settings",
        "COVERAGE_PROCESS_START": str(SETUP_CFG_PATH),
    }

    def test_traceback(self):
        stderr = subprocess.run(
            [
                "python",
                "-m",
                "django",
                "test",
                f"{__name__}.UnitTestRunnerTests.test_traceback",
            ],
            capture_output=True,
            text=True,
            env=self.env,
        ).stderr
        assert "─ locals ─" in stderr

    def test_debug_sql(self):
        stderr = subprocess.run(
            [
                "python",
                "-m",
                "django",
                "test",
                "--debug-sql",
                f"{__name__}.UnitTestRunnerTests.test_assertion",
            ],
            capture_output=True,
            text=True,
        ).stderr
        assert "─ locals ─" in stderr
        assert "Tests can have descriptions." in stderr

    @pytest.mark.skipif(django.VERSION < (3,), reason="--pdb added in Django 3.0")
    def test_pdb(self):
        stderr = subprocess.run(
            [
                "python",
                "-m",
                "django",
                "test",
                "--pdb",
                f"{__name__}.UnitTestRunnerTests.test_assertion",
            ],
            capture_output=True,
            text=True,
        ).stderr
        assert "─ locals ─" in stderr

    def test_django_assertion(self):
        "Django and Unit test modules are hidden in traceback."
        OUTPUT = "─ Traceback (most recent call last) ─"

        stderr = subprocess.run(
            [
                "python",
                "-m",
                "django",
                "test",
                f"{__name__}.UnitTestRunnerTests.test_django_assertion",
            ],
            capture_output=True,
            text=True,
        ).stderr
        assert stderr.count(OUTPUT) == 1
