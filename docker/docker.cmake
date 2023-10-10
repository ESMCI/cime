string(APPEND CXXFLAGS " -std=c++14")
string(APPEND CXX_LIBS " -lstdc++")
string(APPEND FFLAGS " -I/opt/conda/include")
# required for grid generation tests that use make
string(APPEND SLIBS " -L/opt/conda/lib -lnetcdf -lnetcdff")
set(MPI_PATH "/opt/conda")
if (CMAKE_Fortran_COMPILER_VERSION VERSION_GREATER_EQUAL 10)
  string(APPEND FFLAGS " -fallow-argument-mismatch  -fallow-invalid-boz ")
endif()
