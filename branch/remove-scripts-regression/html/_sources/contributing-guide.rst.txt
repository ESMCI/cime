.. _contributing-guide:

Contributing Guide
==================

.. contents::
    :local:

Introduction
------------

The `Case` class is the core of the CIME Case Control system. All interactions with a case are performed through this class. The variables used to create and manipulate a case are defined in XML files, and for each XML file, there is a corresponding Python class to interact with it.

XML files that are part of the CIME distribution and are intended to be read-only with respect to a case are typically named `config_something.xml`. The corresponding Python class is named `Something` and can be found in the file `CIME.XML.something.py`. These are referred to as the CIME config classes.

XML files that are part of a case and thus are read/write to a case are typically named `env_whatever.xml`. The corresponding Python modules are `CIME.XML.env_whatever.py`, and the classes are named `EnvWhatever`. These are referred to as the Case env classes.

The `Case` class includes an array of the Case env classes. In the `configure` function and its supporting functions, the case object creates and manipulates the Case env classes by reading and interpreting the CIME config classes.

.. _contributing-guide-running-tests:

Testing
-------
CIME splits its tests into two categories: `unit` and `sys`.

The `unit` category covers doctests and unit tests, while the `sys` category covers regression tests. Tests are named accordingly (e.g., unit tests: `CIME/tests/test_unit*`).

How to run the tests
```````````````````````
.. warning::

    The legacy `scripts_regression_tests.py` entry point has been replaced by `pytest`.

CIME supports running tests using `pytest`. By using `pytest` coverage reports are automatically generated. Install the test requirements, which include `pytest` and `pytest-cov`:

.. code-block:: bash

    pip install -r test-requirements.txt

Common examples
...............
Run all ``sys`` and ``unit`` tests.

.. code-block:: bash

    pytest

Run only ``sys`` tests. Replace ``sys`` with ``unit`` to run only unit tests.

.. code-block:: bash

    pytest CIME/tests/test_sys*

Run a specific test case.

.. code-block:: bash

    pytest CIME/tests/test_unit_case.py

Run a specific test method.

.. code-block:: bash

    pytest CIME/tests/test_unit_case.py::TestCaseSubmit::test_check_case

Code Quality
------------
To ensure code quality we require all code to be linted by `pylint` and formatted using `black`. We run a few other tools to check XML formatting, ending files with newlines and trailing white spaces.

To ensure consistency when running these checks, we require [`pre-commit`](https://pre-commit.com/).

GitHub Actions lint and check the format of each PR, but they do not automatically fix issues. Installing the `pre-commit` [Git hooks](#installing-git-hook-scripts) runs those checks before each commit.

Installing pre-commit
`````````````````````

.. code-block:: bash

    pip install pre-commit

Running pre-commit
``````````````````

.. code-block:: bash

    pre-commit run -a

Installing git hook scripts
```````````````````````````
If you install these scripts then `pre-commit` will automatically run on `git commit`.

.. code-block:: bash

    pre-commit install

Docker container
----------------
CIME provides a container that CI uses to run tests. You can also use it locally for a reproducible environment. The compiler is ``GNU`` and the MPI implementation is ``OpenMPI``.

The image can be pulled from ``ghcr.io`` or built locally. For local builds, set the build context to the root of the CIME repository.

.. code-block:: bash

   docker pull ghcr.io/esmci/cime:latest

   docker build -t ghcr.io/esmci/cime:latest -f docker/Dockerfile .

Running
```````
The container does not include source code, so bind mount the model checkout and choose the model being used. The following example assumes the model is checked out in ``$SRC_PATH``.

.. code-block:: bash

   docker run -it --rm --hostname docker -e CIME_MODEL=e3sm -v ${SRC_PATH}:/root/model -v ./storage:/root/storage -w /root/model/cime ghcr.io/esmci/cime:latest bash

This example will drop into a shell where CIME commands or tests can be run.
The options are broken down below.

- ``--hostname docker`` is required to tell CIME which machine definition to use.
- ``-e CIME_MODEL=e3sm`` defines the model.
- ``-v ${SRC_PATH}:/root/model`` passes through the model source.
- ``-v ./storage:/root/storage`` persists data such as cases, baselines, archive, and inputdata. You can split the bind mounts if you only want to keep specific inputs or outputs.
- ``-w /root/model/cime`` sets the current working directory to CIME's root.
- ``ghcr.io/esmci/cime:latest`` container image.
- ``bash`` the command to run in the container.

You can also run CIME commands or tests without opening a shell.

.. code-block:: bash

   docker run -it --rm --hostname docker -e CIME_MODEL=e3sm -v ${SRC_PATH}:/root/model -v ./storage:/root/storage -w /root/model/cime ghcr.io/esmci/cime:latest pytest CIME/tests/test_unit*

.. code-block:: bash

   docker run -it --rm --hostname docker -e CIME_MODEL=e3sm -v ${SRC_PATH}:/root/model -v ./storage:/root/storage -w /root/model/cime ghcr.io/esmci/cime:latest ./scripts/create_test SMS.f19_g16.S
