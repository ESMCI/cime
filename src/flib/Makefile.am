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
noinst_LTLIBRARIES = libpio_kinds.la libpio_support.la
#libpiodarray.la libpionfatt.la libpionfput.la

# The convenience libraries depends on their source.
libpio_kinds_la_SOURCES = pio_kinds.F90
libpio_support_la_SOURCES = pio_support.F90

# Each mod file depends on the .o file.
pio_kinds.mod: pio_kinds.$(OBJEXT)
pio_support.mod: pio_support.$(OBJEXT)

# Mod files are built and then installed as headers.
MODFILES = pio_kinds.mod pio_support.mod
BUILT_SOURCES = $(MODFILES)
include_HEADERS = $(MODFILES)

CLEANFILES = *.mod
