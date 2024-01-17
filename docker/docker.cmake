string(APPEND CXXFLAGS " -std=c++14")
string(APPEND CXX_LIBS " -lstdc++")

# DEBUGGING variables
# get_cmake_property(_variableNames VARIABLES)
# foreach (_variableName ${_variableNames})
#     message("${_variableName}=${${_variableName}}")
# endforeach()
# message( FATAL_ERROR "EXIT")

# required for grid generation tests that use make
if (CMAKE_SOURCE_DIR MATCHES "^.*TestGridGeneration.*$")
string(APPEND FFLAGS " -I/opt/conda/include")
string(APPEND SLIBS " -L/opt/conda/lib -lnetcdf -lnetcdff")
endif()
