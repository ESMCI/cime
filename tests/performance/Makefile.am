## This is the automake file for building the Fortran performance
## tests for the PIO library.

# Ed Hartnett 4/6/19

# Parallel builds don't currently work in this directory.
.NOTPARALLEL:

# Put together AM_CPPFLAGS and AM_LDFLAGS.
include $(top_srcdir)/set_flags.am

LDADD = libpio_tutil.la	\
${top_builddir}/src/flib/libpiof.la		\
${top_builddir}/src/clib/libpio.la

# Build the test for make check.
bin_PROGRAMS = pioperformance

pioperformance_SOURCES = pioperformance.F90

# Tests will run from a bash script.
#TESTS = run_tests.sh

EXTRA_DIST = CMakeLists.txt gensimple.pl

# Clean up files produced during testing.
CLEANFILES = *.nc *.log *.mod
