
if (COMP_NAME STREQUAL gptl)
    string(APPEND CPPDEFS " -DHAVE_NANOTIME -DBIT64 -DHAVE_SLASHPROC -DHAVE_GETTIMEOFDAY")
endif()

string(APPEND CMAKE_C_FLAGS " -I/opt/spack-envs/view/include -O1 -g -fno-fast-math -frounding-math -fsignaling-nans -fno-inline -fno-aggressive-loop-optimizations")
string(APPEND CMAKE_Fortran_FLAGS " -I/opt/spack-envs/view/include -O1 -g -fno-fast-math -frounding-math -fsignaling-nans -fno-inline -fno-aggressive-loop-optimizations -ffpe-trap=invalid,zero,overflow")
string(APPEND CMAKE_CXX_FLAGS " -I/opt/spack-envs/view/include")

# required for grid generation tests that use make
if (CMAKE_SOURCE_DIR MATCHES "^.*TestGridGeneration.*$")
    string(APPEND FFLAGS " -I/opt/spack-envs/view/include")
    string(APPEND SLIBS " -L/opt/spack-envs/view/lib -lnetcdf -lnetcdff")
endif()

# DEBUGGING variables
# get_cmake_property(_variableNames VARIABLES)
# foreach (_variableName ${_variableNames})
#     message("${_variableName}=${${_variableName}}")
# endforeach()
# message( FATAL_ERROR "EXIT")
