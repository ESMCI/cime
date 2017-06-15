MESSAGE("   + MPEU:")

# Generate config.h by running autoconf in cmake stage
if (NOT EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/../config.h) 

MESSAGE("     - Generating config.h in mct using configure")
execute_process (COMMAND ./configure
                 OUTPUT_FILE ${CMAKE_CURRENT_BINARY_DIR}/../configure.out
                 WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/..)
endif()

# Clean up config.h as part of make clean
set_directory_properties(PROPERTIES ADDITIONAL_MAKE_CLEAN_FILES 
  "${CMAKE_CURRENT_SOURCE_DIR}/../config.h"
)


FILE(GLOB MPEU_SOURCE  *F90 *c)
INCLUDE_DIRECTORIES (${MPI_Fortran_INCLUDE_PATH}
                     ${CMAKE_CURRENT_SOURCE_DIR}/..) #config.h
ADD_LIBRARY (mpeu ${MPEU_SOURCE})

