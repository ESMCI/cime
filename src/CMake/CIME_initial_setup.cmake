# Module used for CIME testing.
#
# This module does some initial setup that must be done BEFORE the 'project'
# line in the main CMakeLists.txt file.

# the following hack searches for where the Macros.cmake file is in the case that
# the case2bld happens
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
