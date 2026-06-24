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
There are two possible methods to run these tests.

.. warning::

    scripts_regression_tests.py is deprecated and will be removed in the future.

pytest
::::::
CIME supports running tests using `pytest`. By using `pytest` coverage reports are automatically generated. `pytest` supports all the same arguments as `scripts_regression_tests.py`, see `--help` for details.

To get started install `pytest` and `pytest-cov`.

.. code-block:: bash

    pip install -r test-requirements.txt
    pip install pytest pytest-cov

Examples
........
Running all the ``sys`` and ``unit`` tests.

.. code-block:: bash

    pytest

Running only ``sys`` tests, ``sys`` can be replaced with ``unit`` to run only unit testing.

.. code-block:: bash

    pytest CIME/tests/test_sys.*

Running a specific test case.

.. code-block:: bash

    pytest CIME/tests/test_unit_case.py

A specific test can be run with the following.

.. code-block:: bash

    pytest CIME/tests/test_unit_case.py::TestCaseSubmit::test_check_case


scripts_regression_tests.py
:::::::::::::::::::::::::::
The `scripts_regression_tests.py` script is located under `CIME/tests`.

You can pass either the module name or the file path of a test.

Examples
........
Running all the ``sys`` and ``unit`` tests.

.. code-block:: bash

    python CIME/tests/scripts_regression_tests.py

Running only ``sys`` tests, ``sys`` can be replaced with ``unit`` to run only unit testing.

.. code-block:: bash

    python CIME/tests/scripts_regression_tests.py CIME/tests/test_sys*

Runnig a specific test case.

.. code-block:: bash

    python CIME/tests/scripts_regression_tests.py CIME.tests.test_unit_case

A specific test can be run with the following.

.. code-block:: bash

    python CIME/tests/scripts_regression_tests.py CIME.tests.test_unit_case.TestCaseSubmit.test_check_case

Code Quality
------------
To ensure code quality we require all code to be linted by `pylint` and formatted using `black`. We run a few other tools to check XML formatting, ending files with newlines and trailing white spaces.

To ensure consistency when running these checks we require the use of [`pre-commit`](https://pre-commit.com/).

Our GitHub actions will lint and check the format of each PR but will not automatically fix any issues. It's up to the developer to resolve linting and formatting issues. We encourage installing `pre-commit`'s [Git hooks](#installing-git-hook-scripts) that will run these checks before code can be committed.

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
CIME provides a container that the CI uses to run all the testing. This container

can also be used to test locally providing a reproducible environment. The

compiler is ``GNU`` and the MPI implementation is ``OpenMPI``.

The image can be pulled from ``ghcr.io``.

.. code-block:: bash

   docker pull ghcr.io/esmci/cime:latest

or can be built locally. The build context needs to be set to the root of the CIME repository.

.. code-block:: bash

   docker build -t ghcr.io/esmci/cime:latest -f docker/Dockerfile .

Running
```````
The container does not provide any source, as such you will need to bind
mount the model+cime directory and define which model is being used. The 
following example assumes the model is checked out in ``$SRC_PATH``.

.. code-block:: bash

   docker run -it --rm --hostname docker -e CIME_MODEL=<model> -v ${SRC_PATH}:/root/model -v ./storage:/root/storage -w /root/model/cime ghcr.io/esmci/cime:latest bash

This example will drop into a shell where CIME commands or tests can be run.
The options are broken down below.

- ``--hostname docker`` is required to tell CIME which machine definition to use.
- ``-e CIME_MODEL=<model>`` defines the model.
- ``-v ${SRC_PATH}:/root/model`` passes through the model source.
- ``-v ./storage:/root/storage`` persist all data; cases, baselines, archive, inputdata. the bind mounts can be broken out if you only want to persist certain input/outputs.
- ``-w /root/model/cime`` set the current working directory to CIME's root.
- ``ghcr.io/esmci/cime:latest`` container image.
- ``bash`` the command to run in the container.

You can even run CIME or testing without a shell.

.. code-block:: bash

   docker run -it --rm --hostname docker -e CIME_MODEL=<model> -v ${SRC_PATH}:/root/model -v ./storage:/root/storage -w /root/model/cime ghcr.io/esmci/cime:latest pytest CIME/tests/test_unit*

.. code-block:: bash

   docker run -it --rm --hostname docker -e CIME_MODEL=<model> -v ${SRC_PATH}:/root/model -v ./storage:/root/storage -w /root/model/cime ghcr.io/esmci/cime:latest ./scripts/create_test SMS.f19_g16.S

