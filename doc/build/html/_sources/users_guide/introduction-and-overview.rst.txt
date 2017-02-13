.. _introduction:


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

The python version must be greater then 2.7 but less the 3.0.  You can check which version of ptyhon you have by typing:
::

   > python --version

**NOTE:**  Part 1 of this user's guide assumes that CIME and necessary input files have already been installed on 
the computer you are using.  If it is not, see Installing CIME.


CIME terms and concepts
=======================

The following concepts are ingrained in CIME and will occur frequently in this documentation.

**full** vs **data** vs **stub** models:
   Most coupled climate models contain sub-models of the atmosphere, ocean, and other systems 
   that each have their own set of equations to solve must all interact with each other through their shared physical
   interfaces.  We refer to those as *full* models.

   CIME recognizes 7 different physical sub-models of a climate model, those are:

       atmosphere, ocean, sea-ice, land surface, river, glacier, wave

   All must be specified to compile an executable within CIME.

   For some climate problems, its necessary to reduce feedbacks within the system
   by replacing a full model with a version that sends and recieves the same variables to and from other models but
   the values sent are not computed from the equations but instead read from files.  The values received are ignored.
   We call these full-model substitutes *data models*" and CIME provides data models for each of the sub-models supported.

   For some configurations, a data model is not needed and so CIME provides *stub* versions that simply occupy the
   required place in the climate execution sequence  and do not send or receive any data.

**component set** or **compset**:
   The sub-models within a climate model are also called *components* of the climate model. We
   say a climate model has an atmosphere component, an ocean component, etc.  CIME supports mixing *full*, *data* and 
   *stub* components together depending on the problem.  The resulting set of components is called the *component set* or *compset*.

**grid set** or **grid**: 
   Each full model must solve its equations on a numerical grid.  CIME allows several models within the system to have different grids.  The resulting set of numerical grids is called the *grid set* or sometimes just the
   *grid* where *grid* is a unique abbreviation denoting a set of numerical grids.  Sometimes the *resolution* will also
   refer to a specific set of grids with different resolutions.

**machine**: 
   The computer you are using to run CIME and build and run the climate model is called the *machine*.  It could be a workstation or 
   a national supercomputer.  The *machine* is typically the UNIX host name but could be any string.

**compiler**: 
   CIME will control compiling the source code (Fortran, C and C++)  of your model in to an executable.  
   Some machines support mutiple compilers and so you may need to specify which one to use.

**case**:
    The most important concept in CIME is a *case*.  To build and excute a CIME-enabled climate model, you have to 
    make choices of compset, grid set, machine and compiler.  The collection of these choices, and any additional customizations
    you may make, is called the *case*.


Setting CIME defaults
=====================

Before using any CIME commands, you should set the CIME_MODEL environmental variable. In csh, this would be:
::

   setenv CIME_MODEL <model>

Where <model> is one of "acme" or "cesm".


