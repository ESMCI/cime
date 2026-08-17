.. _ccs-query-configuration:

Query configuration
===================

.. contents::
    :local:

Before creating a case, you may need to explore your model's CIME configuration. This includes the supported machines, compsets, components, and grids.

Machines
--------
To list all machines supported by the target model, use the following command:

.. code-block:: bash

    ./scripts/query_config --machines

Each machine listed, such as "docker", has a description, operating system (os), compilers, and MPI libraries (mpilibs). The output also includes information about the systems resources.
For example, the output for the "docker" machine may look like this:

::

    Machine(s)

    docker : Docker 
        os              LINUX
        compilers       gnu,gnuX
        mpilibs         openmpi
        pes/node        8
        max_tasks/node  8
        max_gpus/node   0

To display the current machine configuration, use:

.. code-block:: bash

    ./scripts/query_config --machines current

To list a specific machine, replace ``<machine>`` with the machine name in the following command:

.. code-block:: bash

    ./scripts/query_config --machines <machine>

To print the modules and environment variables for a specific machine and compiler, replace ``<machine>`` and ``<compiler>`` with the appropriate names in the following command:

.. code-block:: bash

    ./scripts/query_config --machines <machine> --compiler <compiler>

For example, the output for the "docker" machine with the "gnu" compiler may look like this:

::

    Machine(s)

    docker (gnu) : Docker 
                os              LINUX
                compilers       gnu,gnuX
                mpilibs         openmpi
                pes/node        8
                max_tasks/node  8
                max_gpus/node   0

            Module commands:

            Environment variables:
                OMPI_ALLOW_RUN_AS_ROOT: 1
                OMPI_ALLOW_RUN_AS_ROOT_CONFIRM: 1
                NETCDF_C_PATH: /opt/conda
                NETCDF_FORTRAN_PATH: /opt/conda

Compsets 
--------
To list all compsets supported by the target model, use the following command:

.. code-block:: bash

    ./scripts/query_config --compsets

To print a specific compset, replace ``<compset>`` with the compset name in the following command:

.. code-block:: bash

    ./scripts/query_config --compsets <compset>

Components
----------
To list all components supported by the target model, use the following command:

.. code-block:: bash

    ./scripts/query_config --components

To display the settings for a specific component, replace ``<component>`` with the component name in the following command:

.. code-block:: bash

    ./scripts/query_config --components <component>

Grids 
-----
To list all supported grids for the target model, use the following command:

.. code-block:: bash

    ./scripts/query_config --grids

Adding the ``--long`` option will output detail information about the grid.

.. code-block:: bash

    ./scripts/query_config --grids --long