from __future__ import annotations

import unittest

from django.test import SimpleTestCase


class TracebackTests(SimpleTestCase):
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
