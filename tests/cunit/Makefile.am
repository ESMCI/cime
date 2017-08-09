# Put together AM_CPPFLAGS and AM_LDFLAGS.
#include $(top_srcdir)/lib_flags.am

# Link to our assembled library.
AM_LDFLAGS = ${top_builddir}/src/clib/libpio.la
AM_CPPFLAGS = -I$(top_srcdir)/src/clib

PIO_TESTS = test_async_3proc
test_async_3proc_SOURCES = test_async_3proc.c test_common.c
check_PROGRAMS = $(PIO_TESTS)
TESTS = run_tests.sh
EXTRA_DIST = run_tests.sh

