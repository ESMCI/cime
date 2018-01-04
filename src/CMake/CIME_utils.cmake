# Module used for CIME testing.
#
# This module contains statements that would otherwise be boilerplate in
# most CIME tests. It enables CTest testing, handles the USE_COLOR and
# ENABLE_GENF90 arguments, and includes several other modules.
#
# Some of the things done here must be done AFTER the 'project' line in the main
# CMakeLists.txt file. This assumes that CIME_initial_setup has already been
# included.

#==========================================================================
# Copyright (c) 2013-2014, University Corporation for Atmospheric Research
#
# This software is distributed under a two-clause BSD license, with no
# warranties, express or implied. See the accompanying LICENSE file for
# details.
#==========================================================================

#=================================================
# Enable CTest tests.
#=================================================

enable_testing()

#=================================================
# Color output
#=================================================

option(USE_COLOR "Allow color from the build output." ON)

set(CMAKE_COLOR_MAKEFILE "${USE_COLOR}")

#=================================================
# Compiler info
#=================================================

list(APPEND CMAKE_MODULE_PATH "../pio2/cmake")
set(CMAKE_C_FLAGS "${CPPDEFS} ${CFLAGS}")
set(CMAKE_Fortran_FLAGS "${CPPDEFS} ${FFLAGS}")
set(CMAKE_EXE_LINKER_FLAGS "${LDFLAGS} ${SLIBS}")

include(Compilers)


#=================================================
# GenF90
#=================================================

option(ENABLE_GENF90
  "Use genf90.pl to regenerate out-of-date Fortran files from .in files."
  OFF)

if(ENABLE_GENF90)
  find_program(GENF90 genf90.pl)

  if(NOT GENF90)
    message(FATAL_ERROR "ENABLE_GENF90 enabled, but genf90.pl not found!")
  endif()

endif()

# Preprocessing utility functions.
include(genf90_utils)

#=================================================
# pFUnit
#=================================================

# pFUnit and its preprocessor
find_package(pFUnit)

# Preprocessor and driver handling.
include(pFUnit_utils)

# Need to add PFUNIT_INCLUDE_DIRS to the general list of include_directories
# because we use pfunit's 'throw'.
include_directories("${PFUNIT_INCLUDE_DIRS}")

#=================================================
# Source list and path utilities.
#=================================================

include(Sourcelist_utils)
