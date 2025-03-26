.. _ccs-query-configuration:

Query configuration
===================

.. content::
    :local:

Before creating a case, you may need to explore your model's CIME configuration. This includes the supported machines, compsets, components, and grids.

Machines
--------   
To list all machines supported by the target model, use the following command:

.. code-block:: bash

    ./scripts/query_config --machines

To display the current machine configuration, use:

.. code-block:: bash

    ./scripts/query_config --machines current

To list a specific machine, replace ``<machine>`` with the machine name in the following command:

.. code-block:: bash

    ./scripts/query_config --machines <machine>

To print the modules and environment variables for a specific machine and compiler, replace ``<machine>`` and ``<compiler>`` with the appropriate names in the following command:

.. code-block:: bash

    ./scripts/query_config --machines <machine> --compiler <compiler>

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

To display the settings for a specific grid, replace ``<grid>`` with the grid name in the following command:

.. code-block:: bash

    ./scripts/query_config --grids <grid>

To display the long name of a grid, use the ``--long`` flag:

.. code-block:: bash

    ./scripts/query_config --grids <grid> --long
