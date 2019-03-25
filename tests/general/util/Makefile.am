## This is the automake file for building the Fortran general tests
## for the PIO library.

# Ed Hartnett 3/25/19

# Put together AM_CPPFLAGS and AM_LDFLAGS.
include $(top_srcdir)/set_flags.am

# Build this uninstalled convenience library.
noinst_LTLIBRARIES = libpio_tutil.la

# The convenience libraries depends on their source.
libpio_tutil_la_SOURCES = pio_tutil.F90

pio_tutil.mod: pio_tutil.$(OBJEXT)
BUILT_SOURCES = pio_tutil.mod
