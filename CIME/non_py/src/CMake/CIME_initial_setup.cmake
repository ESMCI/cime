# Module used for CIME testing and related CMake-based builds.
#
# This module does some initial setup that must be done BEFORE the 'project'
# line in the main CMakeLists.txt file.
#
# To skip use of the Macros.cmake file in CMAKE_BINARY_DIR, set the variable
# CIME_SKIP_MACROS to ON before including this file. (If CIME_SKIP_MACROS is undefined
# or OFF, the Macros file will be included.)

if (NOT DEFINED CIME_SKIP_MACROS OR NOT CIME_SKIP_MACROS)
   include(${CMAKE_BINARY_DIR}/Macros.cmake RESULT_VARIABLE FOUND)
   if(NOT FOUND)
     message(FATAL_ERROR "You must generate a Macros.cmake file using CIME's configure")
   endif()
   if(MPILIB STREQUAL "mpi-serial")
     set(CMAKE_C_COMPILER ${SCC})
     set(CMAKE_Fortran_COMPILER ${SFC})
   else()
     set(CMAKE_C_COMPILER ${MPICC})
     set(CMAKE_Fortran_COMPILER ${MPIFC})
   endif()
endif()
