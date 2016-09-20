include (LibMPI)

include_directories("${CMAKE_SOURCE_DIR}/tests/unit")

# Compiler-specific compiler options
if ("${CMAKE_C_COMPILER_ID}" STREQUAL "GNU")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=c99")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c99")
elseif ("${CMAKE_C_COMPILER_ID}" STREQUAL "PGI")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -c99")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -c99")
elseif ("${CMAKE_C_COMPILER_ID}" STREQUAL "Intel")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=c99")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c99")
elseif ("${CMAKE_C_COMPILER_ID}" STREQUAL "Clang")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=c99")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c99")
endif()
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -g -O0")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -O0")

#==============================================================================
#  PREPARE FOR TESTING
#==============================================================================

file (COPY "./input.nl" 
      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
file (COPY "./not_netcdf.ieee" 
      DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
      
#==============================================================================
#  DEFINE THE TARGETS AND TESTS
#==============================================================================

set (SRCS basic_tests.F90
          driver.F90
          global_vars.F90
          ncdf_tests.F90
          nc_set_log_level2.c)
	
add_executable (pio_unit_test EXCLUDE_FROM_ALL ${SRCS})
target_link_libraries (pio_unit_test piof)
if ("${CMAKE_Fortran_COMPILER_ID}" STREQUAL "GNU")
    target_compile_options (pio_unit_test
        PRIVATE -ffree-line-length-none)
endif()

if (NOT PIO_USE_MPI_SERIAL)
  add_executable (test_intercomm2 EXCLUDE_FROM_ALL test_intercomm2.c)
  target_link_libraries (test_intercomm2 pioc)
  add_dependencies (tests test_intercomm2)
  add_executable (test_async_simple EXCLUDE_FROM_ALL test_async_simple.c test_common.c)
  target_link_libraries (test_async_simple pioc)
  add_dependencies (tests test_async_simple)
  # add_executable (test_async_2comp EXCLUDE_FROM_ALL test_async_2comp.c test_common.c)
  # target_link_libraries (test_async_2comp pioc)
  # add_dependencies (tests test_async_2comp)
  add_executable (test_async_3proc EXCLUDE_FROM_ALL test_async_3proc.c test_common.c)
  target_link_libraries (test_async_3proc pioc)
  add_dependencies (tests test_async_3proc)
  add_executable (test_async_4proc EXCLUDE_FROM_ALL test_async_4proc.c test_common.c)
  target_link_libraries (test_async_4proc pioc)
  add_dependencies (tests test_async_4proc)
  add_executable (test_iosystem2 EXCLUDE_FROM_ALL test_iosystem2.c test_common.c)
  target_link_libraries (test_iosystem2 pioc)
  add_dependencies (tests test_iosystem2)
  add_executable (test_darray_async EXCLUDE_FROM_ALL test_darray_async.c)
  target_link_libraries (test_darray_async pioc)
  add_dependencies (tests test_darray_async)
  add_executable (test_file EXCLUDE_FROM_ALL test_file.c)
  target_link_libraries (test_file pioc)
  add_dependencies (tests test_file)
endif ()
add_executable (test_names EXCLUDE_FROM_ALL test_names.c)
target_link_libraries (test_names pioc)
add_executable (test_nc4 EXCLUDE_FROM_ALL test_nc4.c)
target_link_libraries (test_nc4 pioc)
add_executable (test_darray EXCLUDE_FROM_ALL test_darray.c)
target_link_libraries (test_darray pioc)

if (CMAKE_Fortran_COMPILER_ID STREQUAL "NAG")
   set ( CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -mismatch_all" )
#    target_compile_options (gptl
#        PRIVATE -mismatch_all)
endif ()

add_dependencies (tests test_names)
add_dependencies (tests test_darray)
add_dependencies (tests test_nc4)
add_dependencies (tests pio_unit_test)

# Test Timeout (4 min = 240 sec)
set (DEFAULT_TEST_TIMEOUT 240)

if (PIO_USE_MPISERIAL)
    add_test(NAME test_names
        COMMAND test_names)
    add_test(NAME test_nc4
        COMMAND test_nc4)
    add_test(NAME pio_unit_test
        COMMAND pio_unit_test)
    set_tests_properties(pio_unit_test
        PROPERTIES TIMEOUT ${DEFAULT_TEST_TIMEOUT})
else ()
    add_mpi_test(test_darray
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/test_darray
        NUMPROCS 4
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
    add_mpi_test(test_file
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/test_file
        NUMPROCS 4
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
    add_mpi_test(test_intercomm2
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/test_intercomm2
        NUMPROCS 4
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
    add_mpi_test(test_async_simple
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/test_async_simple
        NUMPROCS 2
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
    # add_mpi_test(test_async_2comp
    #     EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/test_async_2comp
    #     NUMPROCS 4
    #     TIMEOUT ${DEFAULT_TEST_TIMEOUT})
    add_mpi_test(test_async_3proc
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/test_async_3proc
        NUMPROCS 3
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
    add_mpi_test(test_async_4proc
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/test_async_4proc
        NUMPROCS 4
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
    add_mpi_test(test_iosystem2
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/test_iosystem2
        NUMPROCS 4
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
    add_mpi_test(test_names
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/test_names
        NUMPROCS 4
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
    add_mpi_test(test_nc4
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/test_nc4
        NUMPROCS 4
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
    add_mpi_test(pio_unit_test
        EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/pio_unit_test
        NUMPROCS 4
        TIMEOUT ${DEFAULT_TEST_TIMEOUT})
endif ()

if (PIO_HDF5_LOGGING) 
    target_compile_definitions (pio_unit_test 
        PUBLIC LOGGING)
endif ()
