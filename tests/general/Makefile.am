## This is the automake file for building the Fortran general tests
## for the PIO library.

# Ed Hartnett 3/25/19

# Parallel builds don't currently work in this directory.
.NOTPARALLEL:

# Put together AM_CPPFLAGS and AM_LDFLAGS.
include $(top_srcdir)/set_flags.am

LDADD = util/libpio_tutil.la	\
${top_builddir}/src/flib/libpiof.la		\
${top_builddir}/src/clib/libpio.la

AM_CPPFLAGS += -I${top_builddir}/tests/general/util

# There is a test utility mod file in this subdir which must be built.
SRCDIRS = util .

# Build this uninstalled convenience library.
noinst_LTLIBRARIES = libpio_rearr_opts.la

# The convenience libraries depends on their source.
libpio_rearr_opts_la_SOURCES = pio_rearr_opts.F90
pio_rearr_opts_tgv.mod: pio_rearr_opts.$(OBJEXT)
BUILT_SOURCES = pio_rearr_opts_tgv.mod

# Build the test for make check.
check_PROGRAMS = pio_init_finalize pio_file_simple_tests	\
pio_file_fail ncdf_simple_tests ncdf_get_put ncdf_fail ncdf_inq	\
pio_rearr pio_rearr_opts2 pio_decomp_tests	\
pio_decomp_tests_1d pio_decomp_tests_2d pio_decomp_tests_3d	\
pio_decomp_frame_tests pio_decomp_fillval pio_iosystem_tests	\
pio_iosystem_tests2 pio_iosystem_tests3

pio_init_finalize_SOURCES = pio_init_finalize.F90
pio_file_simple_tests_SOURCES = pio_file_simple_tests.F90
pio_file_fail_SOURCES = pio_file_fail.F90
ncdf_simple_tests_SOURCES = ncdf_simple_tests.F90
ncdf_get_put_SOURCES = ncdf_get_put.F90
ncdf_fail_SOURCES = ncdf_fail.F90
ncdf_inq_SOURCES = ncdf_inq.F90
pio_rearr_SOURCES = pio_rearr.F90
#pio_rearr_opts_SOURCES = pio_rearr_opts.F90
pio_rearr_opts2_SOURCES = pio_rearr_opts2.F90
pio_decomp_tests_SOURCES = pio_decomp_tests.F90
pio_decomp_tests_1d_SOURCES = pio_decomp_tests_1d.F90
pio_decomp_tests_2d_SOURCES = pio_decomp_tests_2d.F90
pio_decomp_tests_3d_SOURCES = pio_decomp_tests_3d.F90
pio_decomp_frame_tests_SOURCES = pio_decomp_frame_tests.F90
pio_decomp_fillval_SOURCES = pio_decomp_fillval.F90
pio_iosystem_tests_SOURCES = pio_iosystem_tests.F90
pio_iosystem_tests2_SOURCES = pio_iosystem_tests2.F90
pio_iosystem_tests3_SOURCES = pio_iosystem_tests3.F90

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
