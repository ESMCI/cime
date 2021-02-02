dnl initialize autoconf
AC_INIT
AC_CONFIG_SRCDIR([mpi.h])
dnl specify config header file
AC_CONFIG_HEADERS([config.h])
dnl find c compiler, and fort compiler
AC_PROG_CC
AC_PROG_FC

# ARCHIVE COMMAND SIMILAR ACROSS ALL PLATFORMS
AC_ARG_VAR(AR,Archive Command)
if test -z "$AR"; then
   AR="ar cruv"
fi

# RANLIB
AC_ARG_VAR(RANLIB,Archive index update command)
if test -z "$RANLIB"; then
    # Necessary on Darwin to deal with common symbols (particularly when
    # using ifort).
    if test "$SYSDEF"x = DARWINx; then
        RANLIB="ranlib -c"
    else
        AC_PROG_RANLIB
    fi
fi

dnl determine fortran name-mangling
dnl result functions end up in config.h
AC_FC_WRAPPERS

dnl to determine type of integer needed for fortran
AC_CHECK_SIZEOF(long)

dnl these are to specify the possible arguments to configure.
AC_ARG_ENABLE([test-internal],
 [ --enable-test-internal  Specify internal test as opposed to full suite test]
 ,AC_DEFINE([TEST_INTERNAL],[],
  [Perform tests on data copies internally instead of using MPI_Send]))

AC_ARG_ENABLE([info],[ --enable-info  Print extra debugging info],
 AC_DEFINE([INFO],[],[Print extra debug info]))

AC_ARG_ENABLE([fort-real],
 [ --enable-fort-real=SIZE    Specify Fortran real size],
 AC_DEFINE_UNQUOTED([CONFIG_FORT_REAL],[$enable_fort_real],
  [User-set Fortran real size]))
AC_ARG_ENABLE([fort-double],
 [ --enable-fort-double=SIZE  Specify Fortran double size],
  AC_DEFINE_UNQUOTED([CONFIG_FORT_DOUBLE],[$enable_fort_double],
   [User-set Fortran double size]))
AC_ARG_ENABLE([type-checking],
 [ --enable-type-checking     Perform type checking during communications],
 AC_DEFINE([TYPE_CHECKING],[],[Perform type checking during communications]))


# Determine flag for fortran module include path
# taken from the MCT configure

AC_ARG_VAR(INCLUDEFLAG,Fortran compiler flag for specifying module search path)
AC_LANG_PUSH(Fortran)
AX_FC_VERSION()
AC_LANG_POP(Fortran)


if echo $ac_fc_version_output | grep -i absoft >/dev/null 2>&1; then
   echo "Fortran Compiler is Absoft"
   if test -z "$INCLUDEFLAG"; then
      INCLUDEFLAG="-p"
   fi
elif echo $ac_fc_version_output | grep -i workshop >/dev/null 2>&1; then
   echo "Fortran Compiler is Workshop"
   if test -z "$INCLUDEFLAG"; then
      INCLUDEFLAG="-M"
   fi
elif echo $ac_fc_version_output | grep -i pgf >/dev/null 2>&1; then
   echo "Fortran Compiler is Portland Group"
   LIBS="$LIBS -pgf90libs"
elif echo $ac_fc_version_output | grep -i nag >/dev/null 2>&1; then
   echo "Fortran Compiler is NAG"
   CPRDEF="NAG"
   if test -z "$FCFLAGS"; then
     FCFLAGS="-mismatch"
   fi
fi

# Test to see if fortran compiler supports the flag
# -fallow-argument-mismatch flag introduced in gfortran 10.
#
# Also allow support for NAG compiler using the -mismatch_all flag.
#
# See https://github.com/Unidata/netcdf-fortran/issues/212
# See https://github.com/Unidata/netcdf-fortran/issues/218
ac_save_FCFLAGS="$FCFLAGS"
AC_MSG_CHECKING([if Fortran compiler supports allow-mismatch flag])
cat <<EOF >conftest.f90
Program test
USE ISO_C_BINDING, ONLY: C_PTRDIFF_T
End Program
EOF
doit='$FC -c ${FCFLAGS} ${FCFLAGS_f90} -fallow-argument-mismatch conftest.f90'
if AC_TRY_EVAL(doit); then
   nf_allow_mismatch=yes
   FCFLAGS="${FCFLAGS} -fallow-argument-mismatch"
  else
   nf_allow_mismatch=no
fi
AC_MSG_RESULT([$nf_allow_mismatch])
# End testing of gfortan allow-mismatch flags.

AC_MSG_CHECKING([if Fortran compiler supports mismatch_all flag])
cat <<EOF >conftest.f90
Program test
USE ISO_C_BINDING, ONLY: C_PTRDIFF_T
End Program
EOF
doit='$FC -c ${FCFLAGS} ${FCFLAGS_f90} -mismatch_all conftest.f90'
if AC_TRY_EVAL(doit); then
   nf_mismatch_all=yes
   FCFLAGS="${FCFLAGS} -mismatch_all"
  else
   nf_mismatch_all=no
fi
AC_MSG_RESULT([$nf_mismatch_all])

#end testing of NAG mismatch_all flag.

##
# End mismatch checks
##

# INCLUDE FLAG IF NOT ALREADY SET IS MOST LIKELY -I
if test -z "$INCLUDEFLAG"; then
   INCLUDEFLAG="-I"
fi


AC_CONFIG_FILES([Makefile.conf])
AC_OUTPUT
