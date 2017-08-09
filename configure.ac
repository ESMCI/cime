AC_INIT(pio, 2.2.3)
AC_CONFIG_SRCDIR(src/clib/pio_darray.c)
AM_INIT_AUTOMAKE(foreign)

# Libtool initialisation
AC_CONFIG_MACRO_DIR([m4])

AC_PROG_CC

AC_PROG_LIBTOOL

#AC_CHECK_SIZEOF([MPI_Offset], []. [INCLUDES = 'include <mpi.h>'])

AC_DEFINE([SIZEOF_MPI_OFFSET], [8], [netCDF classic library available])
AC_DEFINE([_NETCDF], [1], [netCDF classic library available])
AC_DEFINE([_NETCDF4], [1], [netcdf-4 available])
AC_DEFINE([_PNETCDF], [1], [parallel-netcdf library available])
AC_DEFINE([PIO_VERSION_MAJOR], [2], [parallel-netcdf library available])
AC_DEFINE([PIO_VERSION_MINOR], [2], [parallel-netcdf library available])
AC_DEFINE([PIO_VERSION_PATCH], [3], [parallel-netcdf library available])

AC_CHECK_LIB([netcdf], [nc_create], [], [AC_MSG_ERROR([Can't find or link to the netcdf library.])])
AC_CHECK_LIB([pnetcdf], [ncmpi_create], [], [AC_MSG_ERROR([Can't find or link to the parallel-netcdf library.])])

AC_CONFIG_HEADERS([config.h])

AC_OUTPUT(Makefile src/Makefile src/clib/Makefile)
