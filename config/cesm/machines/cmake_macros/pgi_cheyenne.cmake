string(APPEND SLIBS " -llapack -lblas")
if (MPILIB STREQUAL mpi-serial)
  string(APPEND SLIBS " -ldl")
endif()
