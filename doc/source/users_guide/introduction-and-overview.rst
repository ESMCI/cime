.. _introduction-and-overview:


**************************
Introduction and Overview
**************************

The Common Infrastructure for Modeling the Earth (CIME) provides a UNIX command-line-based user interface for
performing all of the necessary functions to configure, compile and execute an earth system model.  Part 1 of
this guide will explain all of the basic commands needed to get a model running.  

Prerequisites
=============

You should be familiar with the basic concepts of climate modeling.

You should be familiar with UNIX command line terminals and the UNIX development environment.

CIME's commands are python scripts and require a correct version of the Python interpreter to be installed before any use.

The python version must be greater then 2.7 but less the 3.0.  You can check which version of python you have by typing:
::

   > python --version

**NOTE:**  Part 1 of this user's guide assumes that CIME and necessary input files have already been installed on 
the computer you are using.  If it is not, see Installing CIME.


Terms and concepts
=======================

The following concepts are ingrained in CIME and will occur frequently in this documentation.

**component set** or **compset**:
   CIME allows several sub-models and other tools to be linked together in to a climate model. These sub-models and tools are called 
   *components* of the climate model. We say a climate model has an atmosphere component, an ocean component, etc.  
   The resulting set of components is called the *component set* or *compset*.

**active** vs **data** vs **stub** models:
   A component for the atmosphere or ocean that solve a complex set of equations to describe their behavior are called *active* models, and will sometimes be refered to as *prognostic* or *full* models.

   CIME recognizes 7 different active models of a climate model, those are:

       atmosphere, ocean, sea-ice, land surface, river, glacier, wave

   In addition, an "external processing system" or ESP component is also allowed.

   For some climate problems, its necessary to reduce feedbacks within the system by replacing a active model with a 
   version that sends and receives the same variables to and from other models but
   the values sent are not computed from the equations but instead read from files.  The values received are ignored.
   We call these active-model substitutes *data models* and CIME provides data models for each of the supported components.

   For some configurations, a data model is not needed and so CIME provides *stub* versions that simply occupy the
   required place in the climate execution sequence  and do not send or receive any data.

**grid set** or **grid**: 
   Each active model must solve its equations on a numerical grid.  CIME allows several models within the system to have different grids.  The resulting set of numerical grids is called the *grid set* or sometimes just the
   *grid* where *grid* is a unique abbreviation denoting a set of numerical grids.  Sometimes the *resolution* will also
   refer to a specific set of grids with different resolutions.

**machine**: 
   The computer you are using to run CIME and build and run the climate model is called the *machine*.  It could be a workstation or 
   a national supercomputer.  The *machine* is typically the UNIX host name but could be any string.

**compiler**: 
   CIME will control compiling the source code (Fortran, C and C++)  of your model in to an executable.  
   Some machines support multiple compilers and so you may need to specify which one to use.

**case**:
    The most important concept in CIME is a *case*.  To build and execute a CIME-enabled climate model, you have to 
    make choices of compset, grid set, machine and compiler.  The collection of these choices, and any additional customizations
    you may make, is called the *case*.


Setting defaults
=================

Before using any CIME commands, you should set the CIME_MODEL environmental variable. In csh, this would be:
::

   setenv CIME_MODEL <model>

Where <model> is one of "acme" or "cesm".

Directory content
==================

If you use CIME as part of a climate model or stand alone, the content of the cime directory is the same.  

If you are using it as part of
a climate model, cime is usually one of the first subdirectories under the main directory:

.. csv-table:: CIME directory in a climate model
   :header: "Directory or Filename", "Description"
   :widths: 200, 300

   "README, etc.", "typical top-level directory content."
   "components/", "source code for all of the active models."
   "cime/", "All of CIME code"

CIME's content is split in to several subdirectories.
Users should start in the "scripts" subdirectory.

.. csv-table:: CIME directory content
   :header: "Directory or Filename", "Description"
   :widths: 150, 300

   "CMakeLists.txt", "For building with CMake"
   "ChangeLog", "Developer-maintained record of changes to CIME"
   "ChangeLog_template", "template for an entry in ChangeLog"
   "LICENSE.TXT", "The CIME license"
   "README", "Brief intro to CIME"
   "README.md", "README in markdown language"
   "README.unit_testing", "Instructions on running unit tests with CIME"
   "config/", "Shared and model-specific configuration files"
   "scripts/", "The CIME user interface"
   "src/", "Model source code provided by CIME"
   "tests/", "tests"
   "tools/", "Stand-alone tools useful for climate modeling"
   "utils/", "Some perl source code for CIME scripts; see scripts/lib for python version"

Here are some other key subdirectories, down one level in the 
directory structure.

.. csv-table:: Content of some key CIME sub-directories
   :header: "Directory or Filename", "Description"
   :widths: 150, 300

   "config/cesm/", "CESM-specific configuration options"
   "config/acme/", "ACME-specific configuration options"
   "src/components/", "CIME-provided components including data and stub models"
   "src/drivers/", "CIME-provided main driver for a climate model"
   "src/externals/", "Software provided with CIME for building a climate model"
   "src/share/", "Model source code provided by CIME and used by multiple components"
   "scripts/lib/", "Infrastructure source code for CIME scripts and functions"

Discovering available cases
==============================

You can find what compsets, grids and machines your CIME-enabled model supports using the manage_case command found in cime/scripts.  Use the "--help" option for more information.
::

   > ./manage_case --help

Quick Start
==================

If you would like to quickly see how a case is created, configured, built and run with CIME, try these commands (assuming CIME has been ported to your current machine):
::

   > cd cime/scripts
   > ./create_newcase --case mycase --compset X --res f19_g16
   > cd mycase
   > ./case.setup
   > ./case.build
   > ./case submit

The output from each command will be explained in the sections below. You can follow progress by monitoring the CaseStatus file:
::

   > tail CaseStatus

Repeat the above command until you see the message "Run SUCCESSFUL".  This tells you the case finished successfully.

