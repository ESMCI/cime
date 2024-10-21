.. _cime-dir:

******************
Directory content
******************

If you use CIME as part of a climate model or standalone, the content of the **cime** directory is the same.

If you are using it as part of a climate model, **cime** is usually one of the first subdirectories under the main directory.

.. table:: **CIME directory in a climate model**

   ====================== ===================================
   Directory or Filename               Description
   ====================== ===================================
   README, etc.           typical top-level directory content
   components/            source code for active models
   cime/                  All of CIME code
   ====================== ===================================

CIME's content is split into several subdirectories. Users should start in the **scripts/** subdirectory.

.. table::  **CIME directory content**

   ========================== ==================================================================
   Directory or Filename               Description
   ========================== ==================================================================
   **CIME/**	              **The main CIME source**
   CIME/ParamGen              Python tool for generating runtime params
   CIME/Servers		      Scripts to interact with input data servers
   CIME/SystemTests           Scripts for create_test tests.
   CIME/Tools		      Auxillary tools, scripts and functions.
   CMakeLists.txt	      For building with CMake
   CONTRIBUTING.md            Guide for contributing to CIME
   ChangeLog		      Developer-maintained record of changes to CIME
   ChangeLog_template	      Template for an entry in ChangeLog
   LICENSE.TXT		      The CIME license
   MANIFEST.in                
   README.md		      README in markdown language
   conftest.py
   doc			      Documentation for CIME in rst format
   docker		      Container for CIME testing
   **scripts/**		      **The CIME user interface**
   **tools/**		      **Standalone climate modeling tools**
   utils/		      Some Perl source code needed by some prognostic components
   ========================== ==================================================================
