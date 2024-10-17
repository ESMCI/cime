.. on documentation master file, created by
   sphinx-quickstart on Tue Jan 31 19:46:36 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

CIME documentation
==================

The Common Infrastructure for Modeling the Earth (CIME - pronounced
"SEAM") provides two core features; a Case Control System (CCS) for configuring, compiling and executing
Earth System Models, and a framework for system testing an Earth System Model.

Case Control System (CCS)
*************************
There are three components that make the Case Control System.

1. XML files that describe the models, model configuration (components, grids, input-data, etc) and machines.
2. Python module that provides tools for users to create cases, configure their model, build and submit jobs.
3. Addition stand-alone tools useful for Earth System Modeling.

System Testing
**************
CIME provides tooling to run system testing on an Earth System Model. Each test type is defined to exercise a specific behavior
of the model. The tooling provides the ability to create and compare baselines as well as reporting the results of testing.

*NOTE*
******
CIME does **not** contain the source code for any Earth System Model drivers or components. It is typically included alongside the source code of a host model. However, CIME does include pointers to external repositories that contain drivers, data models and other test components. These external components can be easily assembled to facilitate end-to-end system tests of the CIME infrastructure, which are defined in the CIME repository.

.. toctree::
    :maxdepth: 2
    :hidden:
    :caption: For Users

    users_guide/index.rst
    build_cpl/index.rst

.. toctree::
    :maxdepth: 2
    :hidden:
    :caption: For Developers/Contributors

    misc_tools/index.rst
    glossary/index.rst
    Tools_user/index.rst
    xml_files/index.rst
    CIME_api/modules.rst
    Tools_api/modules.rst

CIME is developed by the
`E3SM <https://climatemodeling.science.energy.gov/projects/energy-exascale-earth-system-model>`_ and
`CESM <http://www.cesm.ucar.edu/>`_ projects.
