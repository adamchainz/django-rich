===========
django-rich
===========

.. image:: https://img.shields.io/github/actions/workflow/status/adamchainz/django-rich/main.yml?branch=main&style=for-the-badge
   :target: https://github.com/adamchainz/django-rich/actions?workflow=CI

.. image:: https://img.shields.io/badge/Coverage-100%25-success?style=for-the-badge
  :target: https://github.com/adamchainz/django-rich/actions?workflow=CI

.. image:: https://img.shields.io/pypi/v/django-rich.svg?style=for-the-badge
   :target: https://pypi.org/project/django-rich/

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=for-the-badge
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit

Extensions for using `Rich <https://rich.readthedocs.io/>`__ with Django.

Requirements
------------

Python 3.8 to 3.12 supported.

Django 3.2 to 4.2 supported.

----

**Want to work smarter and faster?**
Check out my book `Boost Your Django DX <https://adamchainz.gumroad.com/l/byddx>`__ which covers many ways to improve your development experience.
I wrote django-rich whilst working on the book!

----

Installation
------------

1. Install with **pip**:

   .. code-block:: sh

       python -m pip install django-rich

None of django-rich’s features are activated by default.
Follow the documentation below to use them.

Reference
---------

``django_rich.management.RichCommand``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A subclass of Django’s |BaseCommand|__ class that sets its ``self.console`` to a Rich |Console|__.
The ``Console`` uses the command’s ``stdout`` argument, which defaults to ``sys.stdout``.
Colourization is enabled or disabled according to Django’s ``--no-color`` and ``--force-color`` flags.

.. |BaseCommand| replace:: ``BaseCommand``
__ https://docs.djangoproject.com/en/stable/howto/custom-management-commands/#django.core.management.BaseCommand

.. |Console| replace:: ``Console``
__ https://rich.readthedocs.io/en/stable/console.html

You can use ``self.console`` like so:

.. code-block:: python

    from django_rich.management import RichCommand


    class Command(RichCommand):
        def handle(self, *args, **options):
            self.console.print("[bold red]Alert![/bold red]")

You can customize the construction of the ``Console`` by overriding the ``make_rich_console`` class attribute.
This should be a callable that returns a ``Console``, such as a |functools.partial|__.
For example, to disable the default-on ``markup`` and ``highlighting`` flags:

.. |functools.partial| replace:: ``functools.partial``
__ https://docs.python.org/3/library/functools.html#functools.partial

.. code-block:: python

    from functools import partial

    from django_rich.management import RichCommand
    from rich.console import Console


    class Command(RichCommand):
        make_rich_console = partial(Console, markup=False, highlight=False)

        def handle(self, *args, **options):
            ...

``django_rich.test.RichRunner``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A subclass of Django's |DiscoverRunner|__ with colourized outputs and `nice traceback rendering <https://rich.readthedocs.io/en/stable/traceback.html>`__.

.. image:: https://raw.githubusercontent.com/adamchainz/django-rich/main/img/RichRunner.png

.. |DiscoverRunner| replace:: ``DiscoverRunner``
__ https://docs.djangoproject.com/en/stable/topics/testing/advanced/#defining-a-test-runner

To use this class, point your |TEST_RUNNER|__ setting to it:

.. |TEST_RUNNER| replace:: ``TEST_RUNNER``
__ https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-TEST_RUNNER

.. code-block:: python

    TEST_RUNNER = "django_rich.test.RichRunner"

You can also use it as a base for further customization.
Since only output is modified, it should combine well with other classes.

The test runner provides the following features:

* Output is colourized wherever possible.
  This includes Rich’s default `highlighting <https://rich.readthedocs.io/en/stable/highlighting.html>`__ which will format numbers, quoted strings, URL’s, and more.

* Failures and errors use Rich’s `traceback rendering <https://rich.readthedocs.io/en/stable/traceback.html>`__.
  This displays the source code and local values per frame.
  Each frame also shows the filename and line number, and on many terminals you can click the link to jump to the file at that position.

* Output is also colourized when using the ``--debug-sql`` and ``--pdb`` flags.

* All other flags from Django's DiscoverRunner continue to work in the normal way.

Output Width on CI
~~~~~~~~~~~~~~~~~~

When tests run on your CI system, you might find the output a bit narrow for showing tracebacks correctly.
This is because Rich tries to autodetect the terminal dimensions, and if that fails, it will default to 80 characters wide.
You can override this default with the ``COLUMNS`` environment variable (as per Python’s |shutil.get_terminal_size() function|__):

.. |shutil.get_terminal_size() function| replace:: ``shutil.get_terminal_size()`` function
__ https://docs.python.org/3/library/shutil.html#shutil.get_terminal_size

.. code-block:: console

    $ COLUMNS=120 ./manage.py test
