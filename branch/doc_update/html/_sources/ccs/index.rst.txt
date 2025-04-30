Case Control System (CCS)
=========================

.. contents::
    :local:

Prerequisites
`````````````
- CIME-driven model (E3SM, CESM, etc)
- Access to a machine supported by the model
- Familiarity with basic climate modeling concepts
- Familiarity with UNIX command line terminals and development environment
- Python interpreter >= 3.8

Quick start
```````````
The first thing to do is clone the model repository into ``$SRCROOT``.

All examples will be run from ``$CIMEROOT`` which is should exist under ``$SRCROOT`` e.g. (``$CIMEROOT`` would be ``$SRCROOT/cime``).

Next set the ``CIME_MODEL`` evnironment variable for your model, e.g. ``export CIME_MODEL=e3sm``.

.. note::

  Check if your machine is supported by the model.

  .. code-block:: bash

    ./scripts/query_config --machines

The following command will create a directory ``mycase`` using the ``X`` compset and ``f19_g16`` grid. The machine will be auto-detected but it can be defined with ``--machine <name>``.

.. code-block:: bash

  ./scripts/create_newcase --case mycase --compset X --res f19_g16

After the case is setup, change into the directory ``mycase`` and run the following commands to setup, build and submit the case.

.. code-block:: bash

  ./case.setup
  ./case.build
  ./case.submit

After the case is submitted, the status can be checked with ``cat ./CaseStatus``.

What is a Case?
```````````````
A case is an instance of a global climate model simulation. It is defined by several key elements:
a component set, a model grid, a machine, a compiler, and any additional customizations. Each case
represents a unique configuration and setup for running climate simulations, allowing researchers
to explore various scenarios and configurations.

The following sections will delve into these key components in more detail.

Component set (compset)
:::::::::::::::::::::::
A combination of active, data, and stub components that are linked together to form a climate model.
The CCS allows one to define a *component set* (or *compset*) for a case. The CCS allows one to define
several possible compsets, configure and run them on supported platforms. Here is an example of a compset
``longname`` from E3SM for a fully coupled active case: 

::

    1850SOI_EAM%CMIP6_ELM%CNPRDCTCBCTOP_MPASSI_MPASO_MOSART_SGLC_SWAV

Compset alias
.............
Compset longnames can be long and complex, CCS allows one to deinfe a ``compset alias`` to represent a longname.
The above longname can be referred to as "WCYCL1850" in E3SM.

.. note:: 

     Long ago, CESM established a convention for the first letter in a compset alias based
     on the combination of active, data, and stub components.
     If you see mention of "B-case" or "F-case", it comes from these conventions.
     They pre-date the introduction of a wave model as an option.

    ===  ========================================================================================
    A    All data models
    B    All models fully active with stub glc
    C    Active ocean with data atm, river and sea ice. stub lnd, glc
    D    Active sea ice with data atm, ocean (slab) and river. stub lnd, glc
    E    Active atm, lnd, sea-ice, river, data ocean (slab), stub glc
    F    Active atm, lnd, river, sea-ice (thermodynamics only), data ocean (fixed SST), stub glc
    G    Active ocean and sea ice, data atmosphere and river, stub lnd and glc 
    H    Active ocean and sea ice, data atmosphere, stub lnd, river and glc 
    I    Active land and river model, data atmosphere, stub ocn, sea-ice, glc
    IG   Active land, river and ice-sheet, data atmosphere, stub ocn, sea-ice
    X    All x-compsets (2D sine waves for each component except stub glc; for testing only)
    ===  ========================================================================================

Components
..........
In the CCS a ``component`` is a sub-model that is coupled with other components to constitute a global climate modeling system.

There are 7 domains in the Earth System that are typically represented by components in a coupled climate model. These domains are:

* atmosphere (atm)
* ocean (ocn)
* sea-ice (ice)
* land surface (lnd)
* river (rof)
* ice sheet (glc)
* ocean waves (wav)

.. note::
  
  "GLC" originally meant "glacier model" and is now an ice-sheet model but the GLC letters have stuck.

Components are also referred to as ``sub-models``. The choice of 7 is partly historical and partly determined by the physics of the
Earth System: these 7 components occupy physically distinct domains in the Earth System and/or require different numerical grids for solving.

There are a few additional components that are not related to the Earth System. The *coupler* facilitates the interaction of component models. The *external processing system* and *integrated assessment component* are both optional and interact with component models outside of the *coupler*.

* coupler (cpl)
* external processing system (esp)
* integrated assessment component (iac)

Component Types
'''''''''''''''
For each of the 7 physical components (models), there can be three different implementations in a CIME-driven coupled model.

active
    Solve a complex set of equations to describe the model's behavior. Also called *prognostic* or *full* models.
    These can be full General Circulation Models. Multiple active models might be available (for example MOM and MPAS-ocean to represent the global ocean) but only one ocean or atmosphere model at a time can be used in a component set.

data
    For some climate problems, it is necessary to reduce feedbacks within the system by replacing an active model with a
    version that sends and receives the same variables to and from other models, but with the values read from files rather
    than computed from the equations. The values received are ignored. These active-model substitutes are called *data models*.

stub
    For some configurations, no data model is needed and one instead uses a *stub* version that simply occupies the
    required place in the driver and does not send or receive any data. For example, if you are setting up an aqua-planet case
    you would only need a stub for the land model.

Model grid
::::::::::
Each active model must solve its equations on a numerical grid. CIME allows models within the system to have
different grids. The resulting set of all numerical grids is called the *grid set* or usually just the *grid*. Like
the compset longname, the CCS allows one to define an alias to represent a grid set. This alias is also referred to
as the *grid* or sometimes the *resolution*.

Machine
:::::::
The *machine* is the computer you are using to run CIME to build and run the climate model. It could be a workstation or a supercomputer. The exact name of  *machine* is typically the UNIX hostname but it could be any string. 

Compiler
::::::::
A machine may have one or more versions of Fortran, C, and C++ *compilers* that are needed to compile the model's source code.

Customizations
::::::::::::::
The CCS allows for a number of customizations to be made to a case.


Setting up your environment for CCS
```````````````````````````````````
After you've cloned the model repository, you'll need to set up your environment to use the CCS.

First you'll need to let CIME know which model configuration to use by setting the ``CIME_MODEL`` environment variable. In bash, use **export** as shown and replace
**<model>** with the appropriate text. Current possibilities are "e3sm", "cesm", or "ufs".

::

    export CIME_MODEL=<model>

There are a number of possible ways to set CIME variables.
For variables that can be set in more than one way, the order of precedence is:

- variable appears in a command line argument to a CIME command
- variable is set as an environment variable
- variable is set in ``$HOME/.cime/config`` as explained further :ref:`here<customizing-cime>`.
- variable is set in a ``$CASEROOT`` xml file

.. toctree::
    :maxdepth: 3
    :hidden:

    query-configuration
    user-config
    creating-a-case
    setting-up-a-case
    building-a-case
    running-a-case
    cloning-a-case
    examples/index
    timers
    troubleshooting
    model-configuration/index