## This is the automake file for building the netCDF integration layer
## tests.

# Ed Hartnett 7/3/19

# Put together AM_CPPFLAGS and AM_LDFLAGS.
include $(top_srcdir)/set_flags.am

# Build the test for make check.
check_PROGRAMS = tst_pio_udf

# if RUN_TESTS
# # Tests will run from a bash script.
# TESTS = run_tests.sh
# endif # RUN_TESTS

# Distribute the test script.
#EXTRA_DIST = CMakeLists.txt run_tests.sh input.nl

# Clean up files produced during testing.
#CLEANFILES = *.nc *.log
