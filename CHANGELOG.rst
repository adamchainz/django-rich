=========
Changelog
=========

2.2.0 (2025-09-18)
------------------

* Support Django 6.0.

* Make tracebacks use the full terminal width.

  Thanks to Sébastien Corbin for the report in `Issue #240 <https://github.com/adamchainz/django-rich/issues/240>`__.

2.1.0 (2025-09-09)
------------------

* Support Python 3.14.

* Add some default shell imports from Rich on Django 5.2+: ``rich.inspect()``, ``rich.print()``, ``rich.print_json()``, and ``rich.pretty.pprint()``.

  `PR #267 <https://github.com/adamchainz/django-rich/pull/267>`__.

2.0.0 (2025-05-09)
------------------

* Change ``make_rich_console()`` from a ``partial()`` into a method, to avoid this warning on Python 3.13:

    ``FutureWarning``: ``functools.partial`` will be a method descriptor in future Python versions; wrap it in ``staticmethod()`` if you want to preserve the old behavior

  If you have defined ``make_rich_console`` as a ``partial()`` in your own code, you will need to change it to a method or wrap it with ``staticmethod()``.

1.14.0 (2025-02-06)
-------------------

* Support Django 5.2.

1.13.0 (2024-10-29)
-------------------

* Drop Django 3.2 to 4.1 support.

1.12.0 (2024-10-23)
-------------------

* Improve the type hint for ``RichCommand.make_rich_console`` to support overriding.

* Drop Python 3.8 support.

* Support Python 3.13.

1.11.0 (2024-08-30)
-------------------

* Extend test runner to style subtests, teardown errors, and teardown failures.

  THanks to David Smith in `PR #224 <https://github.com/adamchainz/django-rich/pull/224>`__.

* Use unittest’s traceback cleaning.
  Unnecessary frames will now be hidden, as with vanilla unittest, and ``--pdb`` will skip past them.

  `PR #225 <https://github.com/adamchainz/django-rich/pull/225>`__.

1.10.0 (2024-08-12)
-------------------

* Add a ``shell`` command extension that enables Rich’s pretty-printing.
  Activate this feature by adding ``django_rich`` to your ``INSTALLED_APPS`` setting.

  Thanks to q0w in `PR #78 <https://github.com/adamchainz/django-rich/pull/78>`__.

* Extend test runner to display test durations from |--durations|__ in a Rich table.

  .. |--durations| replace:: ``--durations``
  __ https://docs.djangoproject.com/en/stable/ref/django-admin/#cmdoption-test-durations

  `PR #213 <https://github.com/adamchainz/django-rich/pull/213>`__.

* Make test runner use Rich rules between output sections.

  `PR #216 <https://github.com/adamchainz/django-rich/pull/216>`__.

1.9.0 (2024-06-19)
------------------

* Support Django 5.1.

1.8.0 (2023-10-11)
------------------

* Support Django 5.0.

1.7.0 (2023-07-10)
------------------

* Drop Python 3.7 support.

1.6.0 (2023-06-14)
------------------

* Support Python 3.12.

1.5.0 (2023-02-25)
------------------

* Support Django 4.2.

1.4.0 (2022-06-05)
------------------

* Support Python 3.11.

* Support Django 4.1.

1.3.0 (2022-05-10)
------------------

* Drop support for Django 2.2, 3.0, and 3.1.

1.2.0 (2022-02-25)
------------------

* Add ``django_rich.test.RichRunner``, a custom test runner that uses Rich colouring and tracebacks.

  Thanks to David Smith in `PR #29 <https://github.com/adamchainz/django-rich/pull/29>`__.

1.1.0 (2022-01-10)
------------------

* Drop Python 3.6 support.

1.0.0 (2021-11-25)
------------------

* First version.
