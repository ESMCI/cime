# set(CMAKE_STATIC_LINKER_FLAGS "-cqv")

# DEBUGGING variables
get_cmake_property(_variableNames VARIABLES)
foreach (_variableName ${_variableNames})
    message("${_variableName}=${${_variableName}}")
endforeach()
# message( FATAL_ERROR "EXIT")

if (CMAKE_SOURCE_DIR MATCHES "^.*TestGridGeneration.*$")
    string(APPEND FFLAGS " -I/opt/view/include")
    string(APPEND SLIBS " -L/opt/view/lib -lnetcdf -lnetcdff")
endif()