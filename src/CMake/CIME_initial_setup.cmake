# Module used for CIME testing.
#
# This module does some initial setup that must be done BEFORE the 'project'
# line in the main CMakeLists.txt file.

include(${CMAKE_BINARY_DIR}/../Macros.cmake RESULT_VARIABLE FOUND)
if(NOT FOUND)
  message(FATAL_ERROR "You must generate a Macros.cmake file using CIME's configure")
endif()
message("XXX AGSTMP MPILIB: ${MPILIB}")
if("${MPILIB}" STREQUAL "mpi-serial")
  set(CMAKE_C_COMPILER ${SCC})
  set(CMAKE_Fortran_COMPILER ${SFC})
  message("XXXAAA AGSTMP MPILIB: ${SCC}")
else()
  message("XXXBBB AGSTMP MPILIB: ${MPICC}")
  set(CMAKE_C_COMPILER ${MPICC})
  set(CMAKE_Fortran_COMPILER ${MPIFC})
endif()
