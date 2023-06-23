********************
Church Music Scraper
********************

An example project to scrape church music

|architecture-overview|

Best practices
==============

The project uses the popular `flat-layout <https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#flat-layout>`_ to organize packages and modules.

Setup
======

Setup instructions to use the project.

.. code-block:: bash

    # Replace settings in .env
    cp example.env .env

    python main.py

Development
===========

Setup your dev environment by creating a virtual environment

.. code-block:: bash

    # Windows
    # virtualenv \path\to\.venv -p path\to\specific_version_python.exe
    # C:\Users\!Admin\AppData\Local\Programs\Python\Python310\python.exe -m venv .venv
    # .venv\scripts\activate

    # Linux
    # virtualenv .venv /usr/local/bin/python3.10
    # python3.10 -m venv .venv
    # python3 -m venv .venv
    python3 -m venv .venv
    source .venv/bin/activate

    # Update pip
    python -m pip install --upgrade pip

    deactivate

Install dependencies and configure ``.env``.

.. code-block:: bash

    # Install dependencies
    pip install -r requirements_dev.txt

    # Replace settings in .env
    cp example.env .env

Enable pre-commit scripts.

.. code-block:: bash

    pre-commit install

Style Guidelines
----------------

This project enforces quite strict `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ and `PEP257 (Docstring Conventions) <https://www.python.org/dev/peps/pep-0257/>`_ compliance on all code submitted.

We use `Black <https://github.com/psf/black>`_ for uncompromised code formatting.

Summary of the most relevant points:

- Comments should be full sentences and end with a period.
- `Imports <https://www.python.org/dev/peps/pep-0008/#imports>`_  should be ordered.
- Constants and the content of lists and dictionaries should be in alphabetical order.
- It is advisable to adjust IDE or editor settings to match those requirements.

Use new style string formatting
-------------------------------

Prefer `f-strings <https://docs.python.org/3/reference/lexical_analysis.html#f-strings>`_ over ``%`` or ``str.format``.

.. code-block:: python

    # New
    f"{some_value} {some_other_value}"
    # Old, wrong
    "{} {}".format("New", "style")
    "%s %s" % ("Old", "style")

One exception is for logging which uses the percentage formatting. This is to avoid formatting the log message when it is suppressed.

.. code-block:: python

    _LOGGER.info("Can't connect to the webservice %s at %s", string1, string2)


Testing
--------
You'll need to install the test dependencies and project into your Python environment:

.. code-block:: bash

    pip3 install -r requirements_dev.txt
    pip install --editable .

Now that you have all test dependencies installed, you can run tests on the project:

.. code-block:: bash

    isort .
    codespell  --skip="./.*,*.csv,*.json,*.pyc,./docs/_build/*,./htmlcov/*"
    black main.py
    flake8 main.py
    pylint main.py
    rstcheck README.rst
    pydocstyle main.py


References
==========
* Package Python Projects https://packaging.python.org/en/latest/tutorials/packaging-projects/

.. |architecture-overview| image:: docs/architecture_overview.png
