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
You'll need to have cloned the target model's repository into ``$SRCROOT``.

.. note::

  Check if your machine is supported by the model.

  .. code-block:: bash

    ./cime/scripts/query_config --machines

The following example will create a directory ``mycase`` using the ``X`` compset and ``f19_g16`` grid. The machine is auto-detected from the hostname.

::

  export CIME_MODEL=<model name>
  ./cime/scripts/create_newcase --case mycase --compset X --res f19_g16
  cd mycase
  ./case.setup
  ./case.build
  ./case.submit

Check the status of the case with the following command: ``tail CaseStatus``.

What is a Case?
```````````````

A case is an instance of a global climate model simulation. It is defined by several key elements:
a component set, a model grid, a machine, a compiler, and any additional customizations. Each case
represents a unique configuration and setup for running climate simulations, allowing researchers
to explore various scenarios and configurations.

The following sections will delve into these key components in more detail.

Component set (compset)
:::::::::::::::::::::::
The particular combination of active, data, and stub versions of the 7 components is referred to
as a *component set* or  *compset*. The Case Control System allows one to define
several possible compsets and configure and run them on supported platforms.
Here is an example of a component set *longname* from E3SM for a fully coupled active case: 

::

    1850SOI_EAM%CMIP6_ELM%CNPRDCTCBCTOP_MPASSI_MPASO_MOSART_SGLC_SWAV

Compset alias
.............
Typing a compset longname like the above can be exhausting so the CCS allows defining a shorter *compset alias*
which is a short string that substitutes for the longname. In E3SM, the above longname can be referred to as "WCYCL1850".

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
In CIME, a coupled earth system model is made up of *components* that interact through a coupler and are all controlled by a driver.

In the current version of CIME, there are 7 physical components allowed.

* atmosphere (atm)
* ocean (ocn)
* sea-ice (ice)
* land surface (lnd)
* river (rof)
* ice sheet (glc)
* ocean waves (wav)

.. note::
  
  "GLC" originally meant "glacier model" and is now an ice-sheet model but the GLC letters have stuck.

Components are also referred to as *models*. The choice of 7 is partly historical and partly determined by the physics of the
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

Discovering available pre-defined compsets
``````````````````````````````````````````

Your CIME-driven model likely has many compset and gridset aliases defined for cases that are widely used by the
model developers.

Use the utility ``query_config`` to see which out-of-the-box compsets, components, grids, and machines are available for your model.

To see lists of available compsets, components, grids, and machines, look at the **help** text

::

  ./scripts/query_config --help

To see all available component sets, try

::

  ./scripts/query_config --compsets all

To see compset information where **drv** is the component name

::

  ./scripts/query_config --compsets drv

The output will be similar to this::

     --------------------------------------
     Compset Short Name: Compset Long Name
     --------------------------------------
   A                    : 2000_DATM%NYF_SLND_DICE%SSMI_DOCN%DOM_DROF%NYF_SGLC_SWAV
   ADWAV                : 2000_SATM_SLND_SICE_SOCN_SROF_SGLC_DWAV%CLIMO
   S                    : 2000_SATM_SLND_SICE_SOCN_SROF_SGLC_SWAV_SESP
   ADLND                : 2000_SATM_DLND%SCPL_SICE_SOCN_SROF_SGLC_SWAV
   ADESP_TEST           : 2000_DATM%NYF_SLND_DICE%SSMI_DOCN%DOM_DROF%NYF_SGLC_SWAV_DESP%TEST
   X                    : 2000_XATM_XLND_XICE_XOCN_XROF_XGLC_XWAV
   ADESP                : 2000_DATM%NYF_SLND_DICE%SSMI_DOCN%DOM_DROF%NYF_SGLC_SWAV_DESP
   AIAF                 : 2000_DATM%IAF_SLND_DICE%IAF_DOCN%IAF_DROF%IAF_SGLC_SWAV

Each model component specifies its own definitions of what can appear after the **%**  modifier in the compset longname (for example, **DOM** in **DOCN%DOM**).

To see what supported modifiers are for **DOCN**, run `query_config <../Tools_user/query_config.html>`_ as in this example::

  ./scripts/query_config --component docn

The output will be similar to this::

     =========================================
     DOCN naming conventions
     =========================================

         _DOCN%AQP1 : docn prescribed aquaplanet sst - option 1
        _DOCN%AQP10 : docn prescribed aquaplanet sst - option 10
         _DOCN%AQP2 : docn prescribed aquaplanet sst - option 2
         _DOCN%AQP3 : docn prescribed aquaplanet sst - option 3
         _DOCN%AQP4 : docn prescribed aquaplanet sst - option 4
         _DOCN%AQP5 : docn prescribed aquaplanet sst - option 5
         _DOCN%AQP6 : docn prescribed aquaplanet sst - option 6
         _DOCN%AQP7 : docn prescribed aquaplanet sst - option 7
         _DOCN%AQP8 : docn prescribed aquaplanet sst - option 8
         _DOCN%AQP9 : docn prescribed aquaplanet sst - option 9
          _DOCN%DOM : docn prescribed ocean mode
          _DOCN%IAF : docn interannual mode
         _DOCN%NULL : docn null mode
          _DOCN%SOM : docn slab ocean mode
       _DOCN%SOMAQP : docn aquaplanet slab ocean mode
       _DOCN%SST_AQUAP : docn aquaplanet mode:

For more details on how CIME determines the output for query_config, see :ref:`Component Sets<model_config_compsets>`.

.. toctree::
    :maxdepth: 2
    :hidden:

    user-config
    create-a-case.rst
    setting-up-a-case.rst
    building-a-case.rst
    running-a-case.rst
    cloning-a-case.rst
    cime-change-namelist.rst
    timers.rst
    multi-instance
    troubleshooting.rst
    model/index.rst