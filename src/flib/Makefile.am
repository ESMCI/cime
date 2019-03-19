## This is the automake file to build the PIO Fortran library.
# Ed Hartnett 3/19/19

# The library we are building.
#lib_LTLIBRARIES = libpiof.la

# These linker flags specify libtool version info.
# See http://www.gnu.org/software/libtool/manual/libtool.html#Libtool-versioning
# for information regarding incrementing `-version-info`.
#libpiof_la_LDFLAGS = -version-info 1:0:0

# The library soure files.
#libpiof_la_SOURCES = pio.F90

# Build this uninstalled convenience library.
noinst_LTLIBRARIES = libpio_kinds.la

# The convenience library depends on its source.
libpio_kinds_la_SOURCES = pio_kinds.F90

# Mod file depends on its o file, is built and then installed.
pio_kinds.mod: pio_kinds.$(OBJEXT)
BUILT_SOURCES = pio_kinds.mod
include_HEADERS = pio_kinds.mod

CLEANFILES = *.mod
