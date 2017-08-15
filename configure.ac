AC_INIT(pio, 2.2.3)
AC_CONFIG_SRCDIR(src/clib/pio_darray.c)
AM_INIT_AUTOMAKE([foreign serial-tests])

# Libtool initialisation
AC_CONFIG_MACRO_DIR([m4])

AC_PROG_CC

AC_PROG_LIBTOOL

#AC_CHECK_SIZEOF([MPI_Offset], []. [INCLUDES = 'include <mpi.h>'])

AC_DEFINE([SIZEOF_MPI_OFFSET], [8], [netCDF classic library available])
AC_DEFINE([PIO_USE_MALLOC], [1], [use malloc for memory])
AC_DEFINE([PIO_ENABLE_LOGGING], [1], [log messages from library])
AC_DEFINE([_NETCDF], [1], [netCDF classic library available])
AC_DEFINE([_PNETCDF], [1], [parallel-netcdf library available])
AC_DEFINE([PIO_VERSION_MAJOR], [2], [parallel-netcdf library available])
AC_DEFINE([PIO_VERSION_MINOR], [2], [parallel-netcdf library available])
AC_DEFINE([PIO_VERSION_PATCH], [3], [parallel-netcdf library available])
AC_DEFINE([CPRGNU], [1], [defined by CMake build])
AC_DEFINE([HAVE_MPI], [1], [defined by CMake build])
AC_DEFINE([INCLUDE_CMAKE_FCI], [1], [defined by CMake build])
AC_DEFINE([LINUX], [1], [defined by CMake build])
#AC_DEFINE([TIMING], [1], [defined by CMake build])
AC_DEFINE([USE_PNETCDF_VARN], [1], [defined by CMake build])
AC_DEFINE([USE_PNETCDF_VARN_ON_READ], [1], [defined by CMake build])

AC_CHECK_LIB([netcdf], [nc_create], [], [AC_MSG_ERROR([Can't find or link to the netcdf library.])])
AC_CHECK_LIB([pnetcdf], [ncmpi_create], [], [AC_MSG_ERROR([Can't find or link to the parallel-netcdf library.])])

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

AC_CONFIG_HEADERS([config.h])

AC_OUTPUT(Makefile
          src/Makefile
          src/clib/Makefile
          tests/Makefile
          tests/cunit/Makefile)
