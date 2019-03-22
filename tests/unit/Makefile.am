## This is the automake file for building the Fortran tests for the
## PIO library.

# Ed Hartnett 3/20/19

# Link to our assembled library.
AM_LDFLAGS = ${top_builddir}/src/clib/libpio.la
AM_CPPFLAGS = -I$(top_srcdir)/src/clib
LDADD = ${top_builddir}/src/clib/libpio.la

# Build the tests for make check.
#check_PROGRAMS = test_intercomm2 test_async_mpi test_spmd


# Tests will run from a bash script.
#TESTS = run_tests.sh

# Distribute the test script.
#EXTRA_DIST = run_tests.sh

# Clean up files produced during testing.
CLEANFILES = *.nc *.log
