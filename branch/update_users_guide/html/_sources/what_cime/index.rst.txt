.. _what-cime:

.. on documentation master file, created by
   sphinx-quickstart on Tue Jan 31 19:46:36 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

#####################################
 What is CIME?
#####################################

.. toctree::
   :maxdepth: 3
   :numbered:

*********
Overview
*********

CIME, pronounced "SEAM", primarily consists of a Case Control System that supports the configuration, compilation, execution, system testing and unit testing of an Earth System Model. The two main components of the Case Control System are:

1. Scripts to enable simple generation of model executables and associated input files for different scientific cases, component resolutions and combinations of full, data and stub components with a handful of commands.
2. Testing utilities to run defined system tests and report results for different configurations of the coupled system.

CIME also contains additional stand-alone tools, including:

1. Parallel regridding weight generation program
2. Scripts to automate off-line load-balancing.
3. Scripts to conduct ensemble-based statistical consistency tests.
4. Netcdf file comparison program (for bit-for-bit).

CIME does **not** contain the source code for any Earth System Model drivers or components. It is typically included alongside the source code of a host model. However, CIME does include pointers to external repositories that contain drivers, data models and other test components. These external components can be easily assembled to facilitate end-to-end system tests of the CIME infrastructure, which are defined in the CIME repository.

*************************
Development
*************************

CIME is developed in an open-source, public repository hosted under the Earth
System Model Computational Infrastructure (ESMCI) organization on
Github at http://github.com/ESMCI/cime.
