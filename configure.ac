## This is the autoconf file for the PIO library.
## Ed Hartnett 8/16/17

# Initialize autoconf and automake.
AC_INIT(pio, 2.2.3)
AC_CONFIG_SRCDIR(src/clib/pio_darray.c)
AM_INIT_AUTOMAKE([foreign serial-tests])

# The m4 directory holds macros for autoconf.
AC_CONFIG_MACRO_DIR([m4])

# Find and learn about the C compiler.
AC_PROG_CC

# Libtool initialisation.
AC_PROG_LIBTOOL

# Always use malloc in autotools builds.
AC_DEFINE([PIO_USE_MALLOC], [1], [use malloc for memory])

# Need to allow user to set this.
AC_DEFINE([PIO_ENABLE_LOGGING], [1], [log messages from library])

# NetCDF (at least classic) is required for PIO to build.
AC_DEFINE([_NETCDF], [1], [netCDF classic library available])

# Is parallel-netcdf library available?
#AC_DEFINE([_PNETCDF], [1], [parallel-netcdf library available])

# The PIO version, again.
AC_DEFINE([PIO_VERSION_MAJOR], [2], [PIO major version])
AC_DEFINE([PIO_VERSION_MINOR], [2], [PIO minor version])
AC_DEFINE([PIO_VERSION_PATCH], [3], [PIO patch version])

# ???
AC_DEFINE([CPRGNU], [1], [defined by CMake build])

# We must have MPI to build PIO.
AC_DEFINE([HAVE_MPI], [1], [defined by CMake build])

# ???
AC_DEFINE([INCLUDE_CMAKE_FCI], [1], [defined by CMake build])

# All builds are on LINUX.
AC_DEFINE([LINUX], [1], [defined by CMake build])

# Check for netCDF library.
AC_CHECK_LIB([netcdf], [nc_create], [], [AC_MSG_ERROR([Can't find or link to the netcdf library.])])

# Check for pnetcdf library.
AC_CHECK_LIB([pnetcdf], [ncmpi_create], [], [])

# If we have parallel-netcdf, then set these as well.
if test x$ac_cv_lib_pnetcdf_ncmpi_create = xyes; then
   AC_DEFINE([_PNETCDF], [1], [parallel-netcdf library available])
   AC_DEFINE([USE_PNETCDF_VARN], [1], [defined by CMake build])
   AC_DEFINE([USE_PNETCDF_VARN_ON_READ], [1], [defined by CMake build])
fi

# Do we have a parallel build of netCDF-4?
AC_COMPILE_IFELSE([AC_LANG_PROGRAM([#include "netcdf_meta.h"],
[[#if !NC_HAS_PARALLEL
# error
#endif]
])], [have_netcdf_par=yes], [have_netcdf_par=no])

AC_MSG_CHECKING([whether netCDF provides parallel IO])
AC_MSG_RESULT([${have_netcdf_par}])
if test x$have_netcdf_par = xyes; then
  AC_DEFINE([_NETCDF4],[1],[Does netCDF library provide netCDF-4 with parallel access])
fi

# Not working for some reason, so I will just set it...
AC_CHECK_TYPE([MPI_Offset], [], [], [#include <mpi.h>])
if test "x${ac_cv_type_MPI_Offset}" = xyes; then
   AC_CHECK_SIZEOF([MPI_Offset], [], [#include <mpi.h>])
else
   AC_MSG_ERROR([Unable to find type MPI_Offset in mpi.h])
fi

#AC_CHECK_SIZEOF([MPI_Offset], [], [[#include <mpi.h>]])
#AC_DEFINE([SIZEOF_MPI_OFFSET], [8], [netCDF classic library available])

# Create the config.h file.
AC_CONFIG_HEADERS([config.h])

# Create the makefiles.
AC_OUTPUT(Makefile
          src/Makefile
          src/clib/Makefile
          tests/Makefile
          tests/cunit/Makefile)
