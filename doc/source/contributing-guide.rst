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
CIME splits it's testing into two categories `unit` and `sys`.

The `unit` category covers both doctests and unit tests. While the `sys` category covers regression tests. The tests are named accordingly e.g. `unit` tests are found as `CIME/tests/test_unit*`.

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

    pip install pytest pytest-cov
    # or
    # conda install -c conda-forge pytest pytest-cov

Examples
........
Runing all the ``sys`` and ``unit`` tests.

.. code-block:: bash

    pytest

Running only ``sys`` tests, ``sys`` can be replaced with ``unit`` to run only unit testing.

.. code-block:: bash

    pytest CIME/tests/test_sys.*

Runnig a specific test case.

.. code-block:: bash

    pytest CIME/tests/test_unit_case.py

A specific test can be ran with the followin.

.. code-block:: bash

    pytest CIME/tests/test_unit_case.py::TestCaseSubmit::test_check_case


scripts_regression_tests.py
:::::::::::::::::::::::::::
The `scripts_regression_tests.py` script is located under `CIME/tests`.

You can pass either the module name or the file path of a test.

Examples
........
Runing all the ``sys`` and ``unit`` tests.

.. code-block:: bash

    python CIME/tests/scripts_regression_tests.py

Running only ``sys`` tests, ``sys`` can be replaced with ``unit`` to run only unit testing.

.. code-block:: bash

    python CIME/tests/scripts_regression_tests.py CIME/tests/test_sys*

Runnig a specific test case.

.. code-block:: bash

    python CIME/tests/scripts_regression_tests.py CIME.tests.test_unit_case

A specific test can be ran with the followin.

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

    pip install pre_commit
    # or
    # conda install -c conda-forge pre_commit

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
GitHub actions runs all CIME's tests in containers. The dockerfile can be found under the `docker/` directory.

You can skip building the container and use the same container from the GitHub actions using the following commands. This will pull the latest [image](https://hub.docker.com/r/jasonb87/cime/tags), see the available [run modifiers](#running-the-container) to customize the container.

The current container supports the ``GNU`` compiler and ``OpenMPI`` library.

Running
```````
The default environment is similar to the one used by GitHub Actions. It will clone CIME into `/src/cime`, set `CIME_MODEL=cesm` and run CESM's `checkout_externals`. This will create a minimum base environment to run both unit and system tests.

The `CIME_MODEL` environment vairable will change the environment that is created.

Setting it to `E3SM` will clone E3SM into `/src/E3SM`, checkout the submodules and update the CIME repository using `CIME_REPO` and `CIME_BRANCH`.

Setting it to `CESM` will clone CESM into `/src/CESM`, run `checkout_externals` and update the CIME repository using `CIME_REPO` and `CIME_BRANCH`.

The container can further be modified using the environment variables defined below.

.. code-block:: bash

    docker run -it --name cime --hostname docker cime:latest bash


.. code-block:: bash

    docker run -it --name cime --hostname docker -e CIME_MODEL=e3sm cime:latest bash

.. note::
    
    It's recommended when running the container to pass `--hostname docker` as it will match the custom machine defined in `config_machines.xml`. If this is omitted, `--machine docker` must be passed to CIME commands in order to use the correct machine definition.

Environment variables
:::::::::::::::::::::

Environment variables to modify the container environment.

| Name | Description | Default |
| ---- | ----------- | ------- |
| INIT | Set to false to skip init | true |
| GIT_SHALLOW | Performs shallow checkouts, to save time | false |
| UPDATE_CIME | Setting this will cause the CIME repository to be updated using `CIME_REPO` and `CIME_BRANCH` | "false" |
| CIME_MODEL | Setting this will change which environment is loaded | |
| CIME_REPO | CIME repository URL | https://github.com/ESMCI/cime |
| CIME_BRANCH | CIME branch that will be cloned | master |
| E3SM_REPO | E3SM repository URL | https://github.com/E3SM-Project/E3SM |
| E3SM_BRANCH | E3SM branch that will be cloned | master |
| CESM_REPO | CESM repository URL | https://github.com/ESCOMP/CESM |
| CESM_BRANCH | CESM branch that will be cloned | master |

Examples
::::::::
.. code-block:: bash
    
    docker run -it -e INIT=false cime:latest bash

.. code-block:: bash
    
    docker run -it -e CIME_REPO=https://github.com/user/cime -e CIME_BRANCH=updates_xyz cime:latest bash

Persisting data
:::::::::::::::

The `config_machines.xml` definition as been setup to provided persistance for inputdata, cases, archives and tools. The following paths can be mounted as volumes to provide persistance.

* /storage/inputdata
* /storage/cases
* /storage/archives
* /storage/tools

.. code-block:: bash

    docker run -it -v ${PWD}/data-cache:/storage/inputdata cime:latest bash

It's also possible to persist the source git repositories.

.. code-block:: bash

    docker run -it -v ${PWD}/src:/src cime:latest bash

Local git respositories can be mounted as well.

.. code-block:: bash

    docker run -v ${PWD}:/src/cime cime:latest bash

    docker run -v ${PWD}:/src/E3SM cime:latest bash

Building
````````
The container provides 3 targets.

* base - Base image with no batch system.
* slurm - Slurm batch system with configuration and single queue.
* pbs - PBS batch system with configuration and single queue.

.. code-block:: bash
    
    docker build -t ghcr.io/ESMCI/cime:latest --target <target> docker/

Customizing
:::::::::::
When building the container some features can be customized. Multiple `--build-arg` arguments can be passed.

.. code-block:: bash
    
    docker build -t ghcr.io/ESMCI/cime:latest --build-arg {name}={value} docker/

+------------------------+-----------------------------------------------+---------+
| Argument               | Description                                   | Default |
+========================+===============================================+=========+
| MAMBAFORGE_VERSION     | Version of the condaforge/mambaforge image    | 4.11.0-0|
|                        | used as a base                                |         |
+------------------------+-----------------------------------------------+---------+
| PNETCDF_VERSION        | Parallel NetCDF version to build              | 1.12.1  |
+------------------------+-----------------------------------------------+---------+
| LIBNETCDF_VERSION      | Version of libnetcdf, the default will        | 4.8.1   |
|                        | install the latest                            |         |
+------------------------+-----------------------------------------------+---------+
| NETCDF_FORTRAN_VERSION | Version of netcdf-fortran, the default will   | 4.5.4   |
|                        | install the latest                            |         |
+------------------------+-----------------------------------------------+---------+
| ESMF_VERSION           | Version of ESMF, the default will install the | 8.2.0   |
|                        | latest                                        |         |
+------------------------+-----------------------------------------------+---------+
