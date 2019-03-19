## This is the automake file to build the PIO Fortran library.
# Ed Hartnett 3/19/19

# Turn off parallel builds in this directory.
.NOTPARALLEL:

# The library we are building.
lib_LTLIBRARIES = libpiof.la

# These linker flags specify libtool version info.
# See http://www.gnu.org/software/libtool/manual/libtool.html#Libtool-versioning
# for information regarding incrementing `-version-info`.
libpiof_la_LDFLAGS = -version-info 1:0:0

# The library soure files.
libpiof_la_LIBADD = libpio_types.la libpio_nf.la libpio_kinds.la	\
libpio_support.la libpiodarray.la libpionfatt.la libpionfget.la		\
libpionfput.la

libpiof_la_SOURCES = pio_types.F90

# Build this uninstalled convenience library.
noinst_LTLIBRARIES = libpio_types.la libpio_nf.la libpio_kinds.la	\
libpio_support.la libpiodarray.la libpionfatt.la libpionfget.la		\
libpionfput.la

# The convenience libraries depends on their source.
libpio_types_la_SOURCES = pio_types.F90
libpio_nf_la_SOURCES = pio_nf.F90
libpio_kinds_la_SOURCES = pio_kinds.F90
libpio_support_la_SOURCES = pio_support.F90
libpiodarray_la_SOURCES = piodarray.F90
libpionfatt_la_SOURCES = pionfatt_mod.F90
libpionfget_la_SOURCES = pionfget_mod.F90
libpionfput_la_SOURCES = pionfput_mod.F90

# Each mod file depends on the .o file.
pio_types.mod: pio_types.$(OBJEXT)
pio_nf.mod: pio_nf.$(OBJEXT)
pio_kinds.mod: pio_kinds.$(OBJEXT)
pio_support.mod: pio_support.$(OBJEXT)
piodarray.mod: piodarray.$(OBJEXT)
pionfatt_mod.mod: pionfatt_mod.$(OBJEXT)
pionfget_mod.mod: pionfget_mod.$(OBJEXT)
pionfput_mod.mod: pionfput_mod.$(OBJEXT)

# Mod files are built and then installed as headers.
MODFILES = pio_types.mod pio_nf.mod pio_kinds.mod pio_support.mod	\
piodarray.mod pionfatt_mod.mod pionfget_mod.mod pionfput_mod.mod
BUILT_SOURCES = $(MODFILES)
include_HEADERS = $(MODFILES)

CLEANFILES = *.mod
