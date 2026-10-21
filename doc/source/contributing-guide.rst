.. _contributing:

######################
Contributing to CIME
######################

The Common Infrastructure for Modeling the Earth (CIME - pronounced "SEAM")
provides a Case Control System for configuring, compiling and executing
Earth system models. It provides access to many tools including testing
utilities, workflow planning and management, archiving capabilities and
analysis tools.

This document provides instructions for contributing to the CIME
project. All contributions are welcome and can be made in various ways.

CIME currently supports both the Community Earth System Model (CESM_) and the
Energy Exascale Earth System Model (E3SM_).

See the CIME documentation at http://esmci.github.io/cime

.. _CESM: http://www.cesm.ucar.edu/

.. _E3SM: https://e3sm.org/

.. _contributing-guide-ai-policy:

AI usage and human review
-------------------------

CIME permits generative AI assistance, but responsibility remains with people.
AI assistance must not shift the work of understanding, debugging, or validating
a contribution onto maintainers. The same quality, licensing, and reproducibility
standards apply whether or not AI is used.

In this policy, ``you`` refers to the human contributor. AI tools assisting with
a contribution should direct their human operator to this policy and remind them
to personally review and understand the complete PR changes before requesting
review. An AI tool must not claim that the operator has done so unless the
operator confirms it.

Human review before requesting review
`````````````````````````````````````

Before requesting review, personally review and understand the complete set of
changes in the PR, whether or not AI was used. This includes code, tests,
configuration, documentation, and generated files.

You must be able to explain why the changes are correct, how they fit CIME, and
how they were validated. AI review and passing automated checks do not replace
human understanding or project review. You remain responsible for your
contribution and for personally addressing review feedback.

PR descriptions, comments, and review responses must reflect your own reasoning
and understanding. Translation, grammar, and phrasing assistance are welcome,
provided you verify the meaning. Do not submit unreviewed AI output or delegate
conversations with maintainers to an agent.

Disclosure in pull requests
```````````````````````````

Every PR must state whether generative AI was used in preparing the contribution,
including research, code, tests, documentation, or language assistance. If AI
was used, briefly describe how it was used; this description is required.
Provider and model are optional. Keep the disclosure current as the PR changes,
even if generated material was subsequently rewritten. Ordinary formatters,
compilers, and test runners do not require AI disclosure.

For example::

    AI used: Yes
    Usage: Suggested XML parsing tests and helped edit documentation.
    Provider (optional): Anthropic
    Model (optional): Claude Opus 5.5 (extra-high effort)

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

Ways to contribute
------------------

There are various ways to contribute to the CIME project.

Bug reports and feature requests
`````````````````````````````````

CIME uses the git issue tracker on github to track bugs and feature requests.
If you find a bug or have a feature request, please open an issue at https://github.com/ESMCI/cime/issues

Documentation improvements
```````````````````````````

CIME documentation is written using Sphinx and is hosted at http://esmci.github.io/cime

Documentation is an important aspect of CIME that we often don't give
enough time to. If you find any documentation that is unclear, incorrect,
or missing, please consider contributing a documentation fix.

Code contributions
``````````````````

CIME welcomes code contributions. Please read the rest of this document
for information on how to contribute code.

Development model
-----------------

CIME uses the Github development model. The master branch is the main
development branch. All contributions are made via pull requests. Pull
requests should be made against the master branch.

Development process
-------------------

1. Fork the CIME repository
2. Create a branch for your feature or bugfix
3. Make your changes
4. Add tests for your changes
5. Make sure all tests pass
6. Push your changes to your fork
7. Open a pull request

Running Python tests
--------------------

Use the repository test helper to run the complete Python unit- or system-test
suite in a suitable environment::

    ./devtools/run_tests unit
    ./devtools/run_tests system
    ./devtools/run_tests all

Pass one or more pytest paths or node IDs after ``--`` to run selected tests
instead of the complete suite::

    ./devtools/run_tests unit -- CIME/tests/test_unit_utils.py CIME/tests/test_unit_machines.py::TestMachines::test_machine_name

The ``all`` suite runs unit and system tests in one pytest process and reports
their aggregate coverage together. Coverage measures the ``CIME`` package;
test modules are excluded from the report. As with the system suite, running
``all`` on a batch-enabled host requires user approval before passing
``--allow-batch``.

The helper prefers a host machine recognized by ``query_config``. Otherwise,
it uses Docker or Podman when available; unit tests can fall back to the
``linux-generic`` machine and a local Python virtual environment. System tests
require a full E3SM or CESM source checkout and either a matching host machine
or a container runtime. The default container image is
``ghcr.io/esmci/cime:latest``; use ``--build-image`` to build the local test
image with Docker BuildKit instead (for example, ``./devtools/run_tests system
--backend docker --build-image``).

System tests populate a versioned input-data cache under the user's cache
directory from the image tagged in ``docker/INPUTDATA_VERSION``. Test artifacts
are written to a temporary directory, and ``--no-teardown`` is enabled so the
cases and logs remain available for inspection. The helper prints the artifact
directory and retains it after the run. Use ``--artifact-dir`` to choose a
specific new directory, or ``--cache-dir`` to override the cache location.
Pytest's native output includes the test status summary and a terminal coverage
table with missing lines.

On a batch-enabled host, system tests stop unless ``--allow-batch`` is passed.
Ask the user for approval before using that option; the helper does not submit
batch jobs without it. Container tests use the container's non-batch machine
configuration.

Podman storage on an NFS-backed home directory can fail while unpacking an
image because the filesystem lacks extended-attribute support. Configure Podman
storage on a site-provided local scratch filesystem, then pass its configuration
to the helper. For example, when ``$TMPDIR`` is xattr-capable::

    mkdir -p "$TMPDIR/podman"/{graphroot,runroot}
    cat > "$TMPDIR/podman-storage.conf" <<'EOF'
    [storage]
    driver = "overlay"
    graphroot = "$TMPDIR/podman/graphroot"
    runroot = "$TMPDIR/podman/runroot"
    EOF
    ./devtools/run_tests unit --backend podman \
        --podman-storage-conf "$TMPDIR/podman-storage.conf"

The storage location must remain available for the complete test run. Consult
your site's container documentation when ``$TMPDIR`` is unavailable or is not
node-local storage.

Code style
----------

CIME uses the PEP 8 style guide for Python code. Please make sure your
code follows the PEP 8 guidelines. A few guidelines:

- Use 4 spaces for indentation
- Use underscores for function and variable names
- Use CamelCase for class names
- Keep lines under 100 characters where possible

Pre-commit hooks
````````````````

CIME uses pre-commit hooks to help maintain code quality and consistency. We highly recommend installing pre-commit before contributing.

.. code-block:: bash

    pip install pre-commit

If you install these scripts then `pre-commit` will automatically run on `git commit`.

.. code-block:: bash

    pre-commit install

Docker container
----------------
CIME provides a container that the CI uses to run all the testing. This container
can also be used to test locally, providing a reproducible environment. The
compiler is ``GNU`` and the MPI implementation is ``MPICH``. Dependencies are
managed via ``pixi`` and come from ``conda-forge``.

The image can be pulled from ``ghcr.io``.

.. code-block:: bash

   docker pull ghcr.io/esmci/cime:latest

   docker build -t ghcr.io/esmci/cime:latest -f docker/Dockerfile .

.. note::
   The Docker build requires BuildKit. Either set ``DOCKER_BUILDKIT=1`` or
   configure it as the default builder.

.. _contributing-guide-running-tests:

Running
```````
The container does not provide any source, as such you will need to bind
mount the model+cime directory and define which model is being used. The
following example assumes the model is checked out in ``$SRC_PATH``.

.. code-block:: bash

   docker run -it --rm --hostname docker --shm-size=1g \
     -e CIME_MODEL=e3sm \
     -v ${SRC_PATH}:/root/model \
     -v ./storage:/root/storage \
     -w /root/model/cime \
     ghcr.io/esmci/cime:latest bash

This example will drop into a shell where CIME commands or tests can be run.
The options are broken down below.

- ``--hostname docker`` is required to tell CIME which machine definition to use.
- ``--shm-size=1g`` is required when running MPI model tests (not needed for unit tests or build-only). MPICH/UCX use ``/dev/shm`` for shared memory, and Docker's 64MB default is too small.
- ``-e CIME_MODEL=e3sm`` defines the model (must be ``e3sm`` or ``cesm`` in lowercase).
- ``-v ${SRC_PATH}:/root/model`` passes through the model source.
- ``-v ./storage:/root/storage`` persists data such as cases, baselines, archive, and inputdata. Files are created with world-readable permissions so they can be accessed from the host in real-time.
- ``-w /root/model/cime`` sets the current working directory to CIME's root.
- ``ghcr.io/esmci/cime:latest`` container image.
- ``bash`` the command to run in the container.

You can also run CIME commands or tests without opening a shell.

.. code-block:: bash

   docker run -it --rm --hostname docker --shm-size=1g \
     -e CIME_MODEL=e3sm \
     -v ${SRC_PATH}:/root/model \
     -v ./storage:/root/storage \
     -w /root/model/cime \
     ghcr.io/esmci/cime:latest pytest CIME/tests/test_unit*

.. code-block:: bash

   docker run -it --rm --hostname docker --shm-size=1g \
     -e CIME_MODEL=e3sm \
     -v ${SRC_PATH}:/root/model \
     -v ./storage:/root/storage \
     -w /root/model/cime \
     ghcr.io/esmci/cime:latest \
     ./scripts/create_test SMS.f19_g16.X --pesfile /root/.cime/config_pes.xml

.. note::
   When running system tests in the container, use ``--pesfile /root/.cime/config_pes.xml``
   to prevent PE layout overflow. The container dynamically sizes MPI tasks to match
   available cores. See `docker/README.md <https://github.com/ESMCI/cime/blob/master/docker/README.md>`_
   for more details on PE layout and core count management.

Troubleshooting
```````````````

**"CIME_MODEL is not set" error**
   Make sure you pass ``-e CIME_MODEL=e3sm`` or ``-e CIME_MODEL=cesm`` (lowercase).

**Out of memory errors during MPI runs**
   Add ``--shm-size=1g`` or larger. MPICH uses ``/dev/shm`` for shared memory.

**Container core count mismatch**
   Use ``--cpus=N`` to limit container CPU allocation and match your test requirements.

For complete Docker documentation, see ``docker/README.md`` in the repository.

Using Podman
````````````
Podman can be used as a drop-in replacement for Docker. Use ``podman unshare`` to run commands within Podman's user namespace, allowing access to files created in bind mounts.

.. code-block:: bash

   podman run -it --rm --hostname docker --shm-size=1g \
     -e CIME_MODEL=e3sm \
     -v ${SRC_PATH}:/root/model \
     -v ./storage:/root/storage \
     -w /root/model/cime \
     ghcr.io/esmci/cime:latest bash

Run tests directly:

.. code-block:: bash

   podman run -it --rm --hostname docker --shm-size=1g \
     -e CIME_MODEL=e3sm \
     -v ${SRC_PATH}:/root/model \
     -v ./storage:/root/storage \
     -w /root/model/cime \
     ghcr.io/esmci/cime:latest \
     ./scripts/create_test SMS.f19_g16.X --pesfile /root/.cime/config_pes.xml
