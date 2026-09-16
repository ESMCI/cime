.. _contributing-guide:

Contributing Guide
==================

.. contents::
    :local:

.. _contributing-guide-ai-policy:

AI usage and human review
-------------------------

CIME permits generative AI assistance, but responsibility remains with people.
AI assistance must not shift the work of understanding, debugging, or validating
a contribution onto maintainers. The same quality, licensing, and reproducibility
standards apply whether or not AI is used.

Human review of every commit
````````````````````````````

Before submitting a PR, personally review and understand every change in every
commit, whether or not AI was used. This includes code, tests, configuration,
documentation, and generated files. Review subsequent changes before submitting
them as PR updates, including changes introduced by rebases or conflict
resolution. This is a review-before-submission requirement, not a requirement
for approval before creating local commits.

You must be able to explain why each change is correct, how it fits CIME, and
how it was validated. AI review and passing automated checks do not replace
human understanding or project review. You remain responsible for your
contribution and for personally addressing review feedback.

PR descriptions, comments, and review responses must reflect your own reasoning
and understanding. Translation, grammar, and phrasing assistance are welcome,
provided you verify the meaning. Do not submit unreviewed AI output or delegate
conversations with maintainers to an agent.

Disclosure in pull requests
```````````````````````````

Every PR must state whether generative AI was used in preparing the contribution,
including research, code, tests, documentation, or language assistance. If yes,
list the provider and model for each AI service used. If the model is not exposed
by the service, say ``not exposed`` rather than guessing. A brief description of
usage is optional. Keep the disclosure current as the PR changes, even if
generated material was subsequently rewritten. Ordinary formatters, compilers,
and test runners do not require AI disclosure.

For example::

    AI used: Yes
    Provider: <provider name>
    Model: not exposed
    Usage (optional): Suggested XML parsing tests and helped edit documentation.

Correctness and reproducibility
```````````````````````````````

Test changes appropriately and verify generated documentation, behavior claims,
and expected test results against authoritative sources or reference behavior;
see :ref:`contributing-guide-running-tests`. For CIME workflow changes, consider
effects on case configuration, builds, restarts, and reproducibility. Do not
weaken tests merely to make a change pass. Explain intentional changes to
expected behavior and report tests actually run, their results, and validation
gaps. Documentation-only changes do not
require climate-model runs.

Licensing and sensitive information
```````````````````````````````````

Ensure you have the right to contribute all submitted material under CIME's
applicable licensing terms, and preserve required third-party notices. AI output
is not evidence of originality or license compatibility. Do not share secrets
or restricted material with an AI service without authorization, and follow
applicable institutional and data-use rules.

Reviewability and enforcement
`````````````````````````````

Keep PRs focused and small enough to review. Discuss substantial refactors
or changes to CIME behavior with maintainers before implementing them.
Maintainers may request smaller changes, defer review until disclosure or
validation gaps are addressed, or close contributions that require unreasonable
review effort or whose contributors cannot explain them.

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

   docker run -it --rm --hostname docker -e CIME_MODEL=e3sm -v ${SRC_PATH}:/root/model -v ./storage:/root/storage -w /root/E3SM/cime ghcr.io/esmci/cime:latest bash

This example will drop into a shell where CIME commands or tests can be run.
The options are broken down below.

- ``--hostname docker`` is required to tell CIME which machine definition to use.
- ``-e CIME_MODEL=e3sm`` defines the model.
- ``-v ${SRC_PATH}:/root/E3SM`` passes through the model source.
- ``-v ./storage:/root/storage`` persist all data; cases, baselines, archive, inputdata. the bind mounts can be broken out if you only want to persist certain input/outputs.
- ``-w /root/E3SM/cime`` set the current working directory to CIME's root.
- ``ghcr.io/esmci/cime:latest`` container image.
- ``bash`` the command to run in the container.

You can even run CIME or testing without a shell.

.. code-block:: bash

   docker run -it --rm --hostname docker -e CIME_MODEL=e3sm -v ${SRC_PATH}:/root/model -v ./storage:/root/storage -w /root/E3SM/cime ghcr.io/esmci/cime:latest pytest CIME/tests/test_unit*

.. code-block:: bash

   docker run -it --rm --hostname docker -e CIME_MODEL=e3sm -v ${SRC_PATH}:/root/model -v ./storage:/root/storage -w /root/E3SM/cime ghcr.io/esmci/cime:latest ./scripts/create_test SMS.f19_g16.S
