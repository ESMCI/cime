## This is the automake file for building the Fortran general tests
## for the PIO library.

# Ed Hartnett 3/25/19

# Put together AM_CPPFLAGS and AM_LDFLAGS.
include $(top_srcdir)/set_flags.am

LDADD = util/libpio_tutil.la	\
${top_builddir}/src/flib/libpiof.la		\
${top_builddir}/src/clib/libpio.la

AM_CPPFLAGS += -I${top_builddir}/tests/general/util

SRCDIRS = util

# Build the test for make check.
check_PROGRAMS = pio_init_finalize pio_file_simple_tests	\
pio_file_fail ncdf_simple_tests
pio_init_finalize_SOURCES = pio_init_finalize.F90
pio_file_simple_tests_SOURCES = pio_file_simple_tests.F90
pio_file_fail_SOURCES = pio_file_fail.F90
ncdf_simple_tests_SOURCES = ncdf_simple_tests.F90

# Tests will run from a bash script.
TESTS = run_tests.sh

# Distribute the test script.
EXTRA_DIST = CMakeLists.txt run_tests.sh ncdf_fail.F90.in2		\
ncdf_get_put.F90.in2 ncdf_inq.F90.in2 ncdf_simple_tests.F90.in2		\
pio_decomp_fillval.F90.in2 pio_decomp_frame_tests.F90.in2		\
pio_decomp_tests_1d.F90.in2 pio_decomp_tests_2d.F90.in2			\
pio_decomp_tests_3d.F90.in2 pio_decomp_tests.F90.in2			\
pio_file_fail.F90.in2 pio_file_simple_tests.F90.in2			\
pio_init_finalize.F90.in2 pio_iosystem_tests2.F90.in2			\
pio_iosystem_tests3.F90.in2 pio_iosystem_tests.F90.in2			\
pio_rearr.F90.in2 pio_rearr_opts2.F90.in2 pio_rearr_opts.F90.in2

# Clean up files produced during testing.
CLEANFILES = *.nc *.log
