## This is the automake file for building the netCDF integration layer
## tests.

# Ed Hartnett 7/3/19

# Link to the PIO Fortran and C libraries.
LDADD = ${top_builddir}/src/flib/libpiof.la ${top_builddir}/src/clib/libpioc.la

# Find the pio.mod file.
AM_FCFLAGS = -I${top_builddir}/src/flib

# Build the test for make check.
check_PROGRAMS = ftst_pio
ftst_pio_SOURCES = ftst_pio.f90

if RUN_TESTS
# Tests will run from a bash script.
TESTS = run_tests.sh
endif # RUN_TESTS

# Distribute the test script.
EXTRA_DIST = run_tests.sh

# Clean up files produced during testing.
CLEANFILES = *.nc *.log
