## This is the autoconf file for the PIO library.
## Ed Hartnett 8/16/17

# Initialize autoconf and automake.
AC_INIT(pio, 2.4.0)
AC_CONFIG_SRCDIR(src/clib/pio_darray.c)
AM_INIT_AUTOMAKE([foreign serial-tests])

# The m4 directory holds macros for autoconf.
AC_CONFIG_MACRO_DIR([m4])

# Find and learn about the C compiler.
AC_PROG_CC

# Find and learn about the Fortran compiler.
AC_PROG_FC

# Libtool initialisation.
AC_PROG_LIBTOOL

# Always use malloc in autotools builds.
AC_DEFINE([PIO_USE_MALLOC], [1], [use malloc for memory])

AC_MSG_CHECKING([whether a PIO_BUFFER_SIZE was specified])
AC_ARG_WITH([piobuffersize],
              [AS_HELP_STRING([--with-piobuffersize=<integer>],
                              [Specify buffer size for PIO.])],
            [PIO_BUFFER_SIZE=$with_piobuffersize], [PIO_BUFFER_SIZE=134217728])
AC_MSG_RESULT([$PIO_BUFFER_SIZE])
AC_DEFINE_UNQUOTED([PIO_BUFFER_SIZE], [$PIO_BUFFER_SIZE], [buffer size for darray data.])

# Does the user want to enable logging?
AC_MSG_CHECKING([whether debug logging is enabled])
AC_ARG_ENABLE([logging],
              [AS_HELP_STRING([--enable-logging],
                              [enable debug logging capability (will negatively impact performance). \
			      This debugging feature is probably only of interest to PIO developers.])])
test "x$enable_logging" = xyes || enable_logging=no
AC_MSG_RESULT([$enable_logging])
if test "x$enable_logging" = xyes; then
   AC_DEFINE([PIO_ENABLE_LOGGING], 1, [If true, turn on logging.])
fi


# Does the user want to enable Fortran library?
AC_MSG_CHECKING([whether Fortran library should be build])
AC_ARG_ENABLE([fortran],
              [AS_HELP_STRING([--enable-fortran],
                              [build the PIO Fortran library.])])
test "x$enable_fortran" = xyes || enable_fortran=no
AC_MSG_RESULT([$enable_fortran])
AM_CONDITIONAL(BUILD_FORTRAN, [test "x$enable_fortran" = xyes])

# Does the user want to disable pnetcdf?
AC_MSG_CHECKING([whether pnetcdf is to be used])
AC_ARG_ENABLE([pnetcdf],
              [AS_HELP_STRING([--disable-pnetcdf],
                              [Disable pnetcdf use.])])
test "x$enable_pnetcdf" = xno || enable_pnetcdf=yes
AC_MSG_RESULT([$enable_pnetcdf])
AM_CONDITIONAL(BUILD_PNETCDF, [test "x$enable_pnetcdf" = xyes])

# NetCDF (at least classic) is required for PIO to build.
AC_DEFINE([_NETCDF], [1], [netCDF classic library available])

# The PIO version, again.
AC_DEFINE([PIO_VERSION_MAJOR], [2], [PIO major version])
AC_DEFINE([PIO_VERSION_MINOR], [4], [PIO minor version])
AC_DEFINE([PIO_VERSION_PATCH], [0], [PIO patch version])

# ????
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
if test "x$ac_cv_lib_pnetcdf_ncmpi_create" = xno -a $enable_pnetcdf = yes; then
   AC_MSG_ERROR([Pnetcdf not found. Set CPPFLAGS/LDFLAGS or use --disable-pnetcdf.])
fi

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
AM_CONDITIONAL(BUILD_NETCDF4, [test "x$have_netcdf_par" = xyes])

# Not working for some reason, so I will just set it...
AC_CHECK_TYPE([MPI_Offset], [], [], [#include <mpi.h>])
if test "x${ac_cv_type_MPI_Offset}" = xyes; then
   AC_CHECK_SIZEOF([MPI_Offset], [], [#include <mpi.h>])
else
   AC_MSG_ERROR([Unable to find type MPI_Offset in mpi.h])
fi

#AC_CHECK_SIZEOF([MPI_Offset], [], [[#include <mpi.h>]])
#AC_DEFINE([SIZEOF_MPI_OFFSET], [8], [netCDF classic library available])

AC_CONFIG_FILES(src/flib/piodarray.F90:src/flib/piodarray.F90.in2)
AC_CONFIG_FILES(src/flib/pionfatt_mod.F90:src/flib/pionfatt_mod.F90.in2)
AC_CONFIG_FILES(src/flib/pionfget_mod.F90:src/flib/pionfget_mod.F90.in2)
AC_CONFIG_FILES(src/flib/pionfput_mod.F90:src/flib/pionfput_mod.F90.in2)
AC_CONFIG_FILES(tests/general/ncdf_fail.F90:tests/general/ncdf_fail.F90.in2)
AC_CONFIG_FILES(tests/general/ncdf_get_put.F90:tests/general/ncdf_get_put.F90.in2)
AC_CONFIG_FILES(tests/general/ncdf_inq.F90:tests/general/ncdf_inq.F90.in2)
AC_CONFIG_FILES(tests/general/ncdf_simple_tests.F90:tests/general/ncdf_simple_tests.F90.in2)
AC_CONFIG_FILES(tests/general/pio_decomp_fillval.F90:tests/general/pio_decomp_fillval.F90.in2)
AC_CONFIG_FILES(tests/general/pio_decomp_frame_tests.F90:tests/general/pio_decomp_frame_tests.F90.in2)
AC_CONFIG_FILES(tests/general/pio_decomp_tests_1d.F90:tests/general/pio_decomp_tests_1d.F90.in2)
AC_CONFIG_FILES(tests/general/pio_decomp_tests_2d.F90:tests/general/pio_decomp_tests_2d.F90.in2)
AC_CONFIG_FILES(tests/general/pio_decomp_tests_3d.F90:tests/general/pio_decomp_tests_3d.F90.in2)
AC_CONFIG_FILES(tests/general/pio_decomp_tests.F90:tests/general/pio_decomp_tests.F90.in2)
AC_CONFIG_FILES(tests/general/pio_file_fail.F90:tests/general/pio_file_fail.F90.in2)
AC_CONFIG_FILES(tests/general/pio_file_simple_tests.F90:tests/general/pio_file_simple_tests.F90.in2)
AC_CONFIG_FILES(tests/general/pio_init_finalize.F90:tests/general/pio_init_finalize.F90.in2)
AC_CONFIG_FILES(tests/general/pio_iosystem_tests2.F90:tests/general/pio_iosystem_tests2.F90.in2)
AC_CONFIG_FILES(tests/general/pio_iosystem_tests3.F90:tests/general/pio_iosystem_tests3.F90.in2)
AC_CONFIG_FILES(tests/general/pio_iosystem_tests.F90:tests/general/pio_iosystem_tests.F90.in2)
AC_CONFIG_FILES(tests/general/pio_rearr.F90:tests/general/pio_rearr.F90.in2)
AC_CONFIG_FILES(tests/general/pio_rearr_opts2.F90:tests/general/pio_rearr_opts2.F90.in2)
AC_CONFIG_FILES(tests/general/pio_rearr_opts.F90:tests/general/pio_rearr_opts.F90.in2)
AC_CONFIG_FILES(tests/general/pio_tutil.F90:tests/general/util/pio_tutil.F90)

AC_CONFIG_LINKS([tests/general/unit/input.nl:tests/general/unit/input.nl])

# Create the config.h file.
AC_CONFIG_HEADERS([config.h])

# Create the makefiles.
AC_OUTPUT(Makefile
          src/Makefile
          src/clib/Makefile
          src/flib/Makefile
          tests/Makefile
          tests/cunit/Makefile
          tests/unit/Makefile
          tests/general/Makefile
          examples/Makefile
          examples/c/Makefile)
