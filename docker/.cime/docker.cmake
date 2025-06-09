
if (COMP_NAME STREQUAL gptl)
    string(APPEND CPPDEFS " -DHAVE_NANOTIME _DBIT64 -DHAVE_SLASHPROC -DHAVE_GETTIMEOFDAY")
endif()

string(APPEND CMAKE_C_FLAGS_RELEASE " -O2 -g")
string(APPEND CMAKE_Fortran_FLAGS_RELEASE " -O2 -g")
string(APPEND CMAKE_CXX_FLAGS_RELEASE " -O2 -g")

string(APPEND CMAKE_C_FLAGS_DEBUG " -O0")
string(APPEND CMAKE_Fortran_FLAGS_DEBUG " -O0")
string(APPEND CMAKE_CXX_FLAGS_DEBUG " -O0")

# required for grid generation tests that use make
if (CMAKE_SOURCE_DIR MATCHES "^.*TestGridGeneration.*$")
    string(APPEND FFLAGS " -I/opt/conda/envs/$ENV{CIME_MODEL}/include")
    string(APPEND SLIBS " -L/opt/conda/envs/$ENV{CIME_MODEL} -lnetcdf -lnetcdff")
endif()

# DEBUGGING variables
# get_cmake_property(_variableNames VARIABLES)
# foreach (_variableName ${_variableNames})
#     message("${_variableName}=${${_variableName}}")
# endforeach()
# message( FATAL_ERROR "EXIT")
