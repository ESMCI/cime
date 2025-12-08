.. _contributing-guide:

Contributing Guide
==================

.. contents::
    :local:

Introduction
------------

The Community Earth System Model (CIME) is a powerful, community-driven framework designed to support the development, configuration, and execution of Earth system models. As an open-source project, CIME thrives on the contributions of researchers, developers, and users worldwide. Whether you’re fixing a bug, adding new features, improving documentation, or sharing your expertise, your involvement helps advance the scientific community’s ability to understand and simulate Earth’s complex systems. This guide provides everything you need to get started—from setting up your development environment to submitting your first pull request—so you can contribute with confidence and join a vibrant community dedicated to scientific collaboration and innovation.

To get started, you can contribute by fixing issues or answering questions in the community forums. If you’re ready to dive deeper and contribute code, consider exploring these key areas:

- The Case class, which is central to the CIME Configuration System (CCS);
- XML classes, which form the backbone of CCS configuration;
- SystemsTest, used to test models under specific conditions.

**As you add features or bug fixes, remember the importance of adding unit tests.**

Unit tests help ensure that each new change works as intended and doesn’t break existing functionality. By isolating and verifying small units of code, you catch bugs early, reduce the risk of regressions, and make your codebase more maintainable. Unit tests also act as living documentation, clarifying expected behavior for future developers and enabling safer refactoring. Investing in unit tests saves time, improves code quality, and builds confidence in your software’s reliability.

.. _contributing-guide-running-tests:

Testing
-------
CIME splits it's testing into two categories `unit` and `sys`.

- The `unit` category covers both doctests and unit tests.
- The `sys` category covers regression tests.

The tests are named accordingly e.g. `unit` tests are found as `CIME/tests/test_unit*`.

Running the tests
`````````````````
There are two possible methods to run these tests; ``pytest`` and ``scripts_regression_tests``.

To run the tests with ``pytest`` you'll need to install some packages; ``pytest`` and ``pytest-cov``.

.. warning::

    The scripts_regression_tests.py will be deprecated and the preferred method of running tests it ``pytest``.

Unit Testing
::::::::::::
Here's an example for running the unit tests using both methods.

.. code-block:: bash

    pytest CIME/tests/test_unit*

   
.. code-block:: bash

    python CIME/tests/scripts_regression_tests.py CIME/tests/test_unit*

System Testing
::::::::::::::

.. code-block:: bash

    pytest CIME/tests/test_sys*

.. code-block:: bash

    python CIME/tests/scripts_regression_tests.py CIME/tests/test_sys*

Code Quality
------------
**To maintain high code quality and consistency, all code must be linted with Pylint and formatted using Black.** We also use additional tools to enforce proper XML formatting, ensure files end with newlines, and eliminate trailing whitespace.

**To streamline these checks, we require the use of pre-commit.** While our GitHub Actions will automatically lint and check the format of every pull request, they will not fix issues for you—developers are responsible for resolving any linting or formatting errors.

**We strongly recommend installing pre-commit’s Git hooks** to run these checks automatically before each commit, helping you catch and fix issues early.


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
CIME provides a container that is utilized by CI testing and provides developers with a consistent environment they can test in.

This container provides a ``GNU`` compiler, ``OpenMPI`` library and all confguration required to run CIME's testing and build simple test cases. The compiler and libraries in the container is managed using ``Anaconda``. There are currently two preloaded environments; ``e3sm`` and ``cesm``.

.. warning::

    Since CIME is generally provided as a sub-module in a projects repostiory the CIME containers do not provide either the project or CIME code. You'll need to pass these through using a volume.

The provide machine configuration requires you to either set the containers hostname with ``--hostname docker`` or pass ``--machine docker`` to all CIME tooling.

It's usually recommended to use the ``latest`` tag but if an older version is required you can find these at https://github.com/ESMCI/cime/pkgs/container/cime.

Running
```````
The following assumes you've checkouted out your projects code to ``$HOME/model`` and the name of your model is stored in ``$TARGET_MODEL`` environment variable.

.. code-block:: bash

    docker run -it --rm --hostname docker -v "$HOME/model":/home/cime/model -e USER_ID=`id -u` -e GROUP_ID=`id -g` -e CIME_MODEL="$TARGET_MODEL" ghcr.io/esmci/cime:latest bash

.. warning::

    The ``-e USER_ID=`id -u` -e GROUP_ID=`id- g``` is required so the containers uid/gid will match your host machines. This allows the containers user to have the correct permissions to view/edit files and if any new files are created you can access them outside the container.

While running CIME within the continer there may be a need to persist either the inputdata retrieved by CIME or the cases that are created. This can be accomplished using volumes. The following example assumes inputdata will be stored at ``$HOME/CIME/inputdata`` and cases at ``$HOME/CIME/cases``.

.. code-block:: bash

    docker run -it --rm --hostname docker -v "$HOME/model":/home/cime/model -v "$HOME/CIME/inputdata":/home/cime/inputdata -v "$HOME/CIME/cases":/home/cime/cases -e USER_ID=`id -u` -e GROUP_ID=`id -g` -e CIME_MODEL="$TARGET_MODEL" ghcr.io/esmci/cime:latest bash

Environment variables
:::::::::::::::::::::
The following environment variables control some aspects of the cotnainers behavior.

+------------------+--------------------------------------------+---------+
| Name             | Description                                | Default |
+==================+============================================+=========+
| USER_ID          | Sets the container's user id.              | 1000    |
+------------------+--------------------------------------------+---------+
| GROUP_ID         | Sets the container's group id.             | 1000    |
+------------------+--------------------------------------------+---------+
| SKIP_ENTRYPOINT  | Skips entering a new shell as the          | false   |
|                  | container's user.                          |         |
+------------------+--------------------------------------------+---------+

Building
````````
The container provides 3 targets.

* base - Base image with no batch system.
* slurm - Slurm batch system with configuration and single queue.
* pbs - PBS batch system with configuration and single queue.

.. code-block:: bash
    
    docker build -t ghcr.io/ESMCI/cime:latest --target <target> docker/
