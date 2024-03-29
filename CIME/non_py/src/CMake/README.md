CMake_Fortran_utils
===================

CMake modules dealing with Fortran-specific issues and Fortran libraries

Currently, these modules should work with CMake version 2.8.8 and later
versions. Earlier CMake versions may work but are untested.

Below is a brief listing of modules. More detailed information on the
purpose and use of these modules can be found in comments at the top of
each file.

Find modules for specific libraries:

FindNETCDF

FindPnetcdf

Utility modules:

genf90_utils - Generate Fortran code from genf90.pl templates.

Sourcelist_utils - Use source file lists defined over multiple directories.

Modules that are CESM-specific and/or incomplete:

CIME\_initial\_setup - Handles setup that must be done before the 'project'
line. This must be included before the 'project' line in the main CMakeLists.txt
file.

CIME_utils - Handles a few options, and includes several other modules. This
must be included after the 'project' line in the main CMakeLists.txt file, and
after the inclusion of CIME\_initial\_setup.

Compilers - Specify compiler-specific behavior, add build types for CESM.
