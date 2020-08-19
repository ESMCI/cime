include (LibMPI)

include_directories("${CMAKE_SOURCE_DIR}/tests/ncint")
include_directories("${CMAKE_BINARY_DIR}")

#==============================================================================
#  PREPARE FOR TESTING
#==============================================================================

# Don't run these tests if we are using MPI SERIAL.
add_executable (tst_pio_udf EXCLUDE_FROM_ALL tst_pio_udf.c)
add_dependencies (tests tst_pio_udf)
target_link_libraries (tst_pio_udf pioc)

# Test Timeout in seconds.
if (PIO_VALGRIND_CHECK)
  set (DEFAULT_TEST_TIMEOUT 480)
else ()
  set (DEFAULT_TEST_TIMEOUT 240)
endif ()

# All tests need a certain number of tasks, but they should be able to
# run successfully with more than they need. Test this by providing an
# extra processor for each C test.
set (AT_LEAST_TWO_TASKS 3)
set (AT_LEAST_THREE_TASKS 4)
set (AT_LEAST_FOUR_TASKS 5)
set (AT_LEAST_EIGHT_TASKS 9)
set (EXACTLY_FOUR_TASKS 4)

add_mpi_test(tst_pio_udf
  EXECUTABLE ${CMAKE_CURRENT_BINARY_DIR}/tst_pio_udf
  NUMPROCS ${AT_LEAST_FOUR_TASKS}
  TIMEOUT ${DEFAULT_TEST_TIMEOUT})

