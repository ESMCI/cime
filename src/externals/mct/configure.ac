#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_INIT([MCT],[2.10])

# PROCESS THE FOLLOWING MAKEFILES
AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_FILES(Makefile.conf)
AC_CONFIG_HEADERS([config.h])

# DECLARE PACKAGE OPTIONS

AC_ARG_ENABLE(mpiserial,
AS_HELP_STRING([--enable-mpiserial],[Use the included MPI replacement library for single processor]),
[DONOTCHECKMPI="DONOTCHECKMPI"]
)

AC_ARG_ENABLE(debugging,
AS_HELP_STRING([--enable-debugging],[Use the debugging flag and disable the optimization flag]),
[DEBUGGING="ENABLED"]
)

AC_ARG_ENABLE(selectedrealkind,
AS_HELP_STRING([--enable-selectedrealkind],[define single precision and double precision numbers using the selected_real_kind function. Default uses the kind inquiry function.]),
[SRKDEF="SELECTEDREALKIND"]
)

AC_ARG_ENABLE(sequence,
AS_HELP_STRING([--enable-sequence],[Modify MCT types to make them contiguous in memory.]),
[SRKDEF="SEQUENCE"],)

AC_ARG_ENABLE(babel,
AS_HELP_STRING([--enable-babel],[Supply this option if you plan on building the Babel bindings to MCT]),
[SRKDEF="SEQUENCE"],)



# DECLARE THE FOLLOWING PRECIOUS VARIABLES

AC_ARG_VAR(MPILIBS,[MPI library command line invocation])
AC_ARG_VAR(MPIHEADER,[MPI header include path with INCLUDEFLAG])
AC_ARG_VAR(FPP,C-preprocessor for Fortran source code)
AC_ARG_VAR(FPPFLAGS,C-preprocessing flags for Fortran source code)
AC_ARG_VAR(FC,The Fortran compiler)
AC_ARG_VAR(FCFLAGS,User-defined Fortran compiler flags)
AC_ARG_VAR(PROGFCFLAGS,User-defined Fortran compiler flags for example programs)
AC_ARG_VAR(CFLAGS,Customized C source compilation flags)
AC_ARG_VAR(DEBUG,Fortran compiler flag for generating symbolic debugging information)
AC_ARG_VAR(OPT,Fortran compiler flag for optimization level)
AC_ARG_VAR(REAL8,[Fortran compiler flag for setting the default REAL size to REAL(KIND=8)])
AC_ARG_VAR(BIT64,Fortran compiler flag for generating 64-bit objects)
AC_ARG_VAR(ENDIAN,Fortran compiler flag for converting big-endian to little-endian)
AC_ARG_VAR(INCLUDEFLAG,Fortran compiler flag for specifying module search path)
AC_ARG_VAR(INCLUDEPATH,Additional library and module paths with INCLUDEFLAG)
AC_ARG_VAR(AR,Archive command)
AC_ARG_VAR(RANLIB,Archive index update command)
AC_ARG_VAR(BABELROOT,Root directory of your Babel installation. i.e.: $BABELROOT/bin/babel $BABELROOT/lib/libsidl.so)
AC_ARG_VAR(COMPILER_ROOT,Root directory of your FORTRAN compiler)
AC_ARG_VAR(FORT_SIZE, Number of bits in Fortran real and double kind)

# INCLUDE BABELROOT and COMPILER_ROOT in Makefile.conf(autoconf output)
AC_SUBST(BABELROOT)
AC_SUBST(COMPILER_ROOT)
AC_SUBST(PYTHON)
AC_SUBST(PYTHONOPTS)

# SET TEMPORARY VARIABLES

# OS AND PLATFORM NAME
test "$osname"=NONE && osname=`uname -s`
test "$machinename"=NONE && machinename=`uname -m`
fullhostname=`hostname -f`

# START TESTS

# CHECK FOR THE C COMPILER
AC_PROG_CC([cc])

# CHECK FOR BYTE ORDERING
AC_C_BIGENDIAN

# CHECK FOR THE FORTRAN COMPILER
# RLJ- specify the order, include PathScale and do not search for F77
AC_PROG_FC([nagfor xlf95 pgf95 ifort gfortran pathf95 ftn lf95 f95 fort ifc efc xlf90 pgf90 pathf90 epcf90 pghpf])

if test -z "$GFC"; then
   IS_GNU="no"
else
   IS_GNU=$GFC
fi

# CHECK FOR MPI LIBRARIES
AC_LANG_PUSH(Fortran)

AC_FC_SRCEXT(F90)

OLDFCFLAGS="$FCFLAGS"

if test -n "$MPIHEADER"; then
   FCFLAGS="$FCFLAGS $MPIHEADER"
fi

# CHECK MPI BY DEFAULT
if test -z "$DONOTCHECKMPI"; then
   ACX_MPI
fi

# DONT CHECK MPI IF SERIALMPI OPTION IS ENABLED
if test -n "$DONOTCHECKMPI"; then
   echo "MPISERIAL ENABLED: BYPASSING MPI CHECK"
   if test -z "$MPIFC"; then
      MPIFC=$FC
   fi
   if test -z "$FORT_SIZE"; then
      FORT_SIZE="real4double8"
      echo "FORT_SIZE IS PRESET TO $FORT_SIZE"
   fi
   abs_top_builddir=`pwd`
   MPISERPATH=$abs_top_builddir/mpi-serial
   AC_SUBST(MPISERPATH)
   MPIHEADER=-I$MPISERPATH
   MPILIBS="-L$MPISERPATH -lmpi-serial"
fi

FCFLAGS="$OLDFCFLAGS"

# A HACK TO FIX ACX_MPI TO GET MPILIBS TO BE AN EMPTY STRING
if test "$MPILIBS" = " "; then
   MPILIBS=""
fi

# SET FC TO MPIFC. IF MPILIBS IS PRESENT, SET FC TO FC.
if test -z "$FC"; then
   FC=$MPIFC
   if test "$FC" != "$MPIFC";  then
      if test -n "$MPILIBS"; then
	 FC=$FC
      fi
   fi
fi

# FOR SANITY, CHECK THAT FILENAME EXTENSION FOR FC IS CONSISTENT WITH FC
OLDFC="$FC"
FC="$FC"

AC_COMPILE_IFELSE(
  [       subroutine oof()
             return
          end], [],
  [AC_MSG_WARN([$FC FAILED TO COMPILE FILENAME EXTENSION $ac_ext])
  ])



FC="$OLDFC"

# CHECK HOW TO GET THE COMPILER VERSION.
echo "Checking Compiler Version"
AX_FC_VERSION()

AC_LANG_POP(Fortran)

# Check how to use the cpp with fortran

AC_FC_PP_DEFINE()


# CHECK HOW TO NAME MANGLE C FUNCTIONS SO THAT IT CAN BE CALLED FROM FORTRAN
OLDFC="$FC"

AC_FC_WRAPPERS()

FC="$OLDFC"

# CHECK THAT THE FORTRAN COMPILER CAN CORRECTLY PROCESS THESE DIRECTIVES
# IF NOT, USE THE EXTERNAL C PREPROCESSOR
OLDFC="$FC"

defineflag="-Daardvark"
if test "$OLDFC" = "xlf90"; then
   defineflag="-WF,-Daardvark"
fi
if test "$OLDFC" = "frt"; then
   defineflag="-Wp,-Daardvark"
fi

FC="$OLDFC"

# DEFINE VARIABLES ACCORDING TO OS AND COMPILER

echo "Hostname=$ac_hostname"
echo "Machine=$machinename"
echo "OS=$osname"

# CHECK OS NAME
if echo $osname | grep -i aix >/dev/null 2>&1; then
   SYSDEF="AIX"
fi
if echo $osname | grep -i darwin >/dev/null 2>&1; then
   SYSDEF="DARWIN"
fi
if echo $osname | grep -i unix_system_v >/dev/null 2>&1; then
   SYSDEF="UNIXSYSTEMV"
fi
if echo $osname | grep -i irix >/dev/null 2>&1; then
   SYSDEF="IRIX"
fi
if echo $osname | grep -i irix64 >/dev/null 2>&1; then
   SYSDEF="IRIX64"
fi
if echo $osname | grep -i linux >/dev/null 2>&1; then
   SYSDEF="LINUX"
fi
if echo $osname | grep -i osf1 >/dev/null 2>&1; then
   SYSDEF="OSF1"
fi
if echo $osname | grep -i super >/dev/null 2>&1; then
   SYSDEF="SUPERUX"
fi
if echo $osname | grep -i sun >/dev/null 2>&1; then
   SYSDEF="SUNOS"
fi
if echo $osname | grep -i unicos >/dev/null 2>&1; then
   SYSDEF="UNICOS"
fi
if test -z "$SYSDEF"; then
   AC_MSG_WARN([OPERATING SYSTEM UNKNOWN])
   SYSDEF="UNKNOWNOS"
fi

# Set the default FCFLAGS for non-gfortran compilers.
# NOTE:  This may change with a new version of autoconf.
DEFFCFLAGS="-g"

#####################################################
# CHECK COMPILER NAME and add specific flags
if echo $FC | grep xlf >/dev/null 2>&1; then
   echo "Fortran Compiler is XLF"
   CPRDEF="XLF"
   if test -z "$REAL8"; then
      REAL8="-qrealsize=8"
   fi
   if test -z "$OPT"; then
      OPT="-O2 -qarch=auto"
   fi
   if test -z "$DEBUG"; then
      DEBUG="-qdbg"
   fi
   if test "$FCFLAGS" = "$DEFFCFLAGS"; then
       FCFLAGS=""
   fi
elif echo $ac_fc_version_output | grep -i pgfor >/dev/null 2>&1; then
   echo "Fortran Compiler is Portland Group"
   CPRDEF="PGI"
   if test -z "$REAL8"; then
      REAL8="-r8"
   fi
   if test -z "$BIT64"; then
      BIT64="-pc 64"
   fi
   if test "$FCFLAGS" = "$DEFFCFLAGS"; then
      FCFLAGS=""
   fi
   if test -z "$ENDIAN"; then
      ENDIAN="-byteswapio"
   fi
   if test -z "$OPT"; then
      OPT="-O2"
   fi
   if test -z "$DEBUG"; then
      DEBUG="-g"
   fi
elif test "$IS_GNU" = "yes" ; then
# The GNU compiler can hide inside other compilers like ftn
  if echo $ac_fc_version_output | grep -i Cray >/dev/null 2>&1; then
   echo "Fortran Compiler is GNU, Cray"
    CPRDEF="GNU"
  else
    echo "Fortran Compiler is GNU"
    CPRDEF="GNU"
  fi
# For gfortran, default flags are different
    if test "$FCFLAGS" = "-g -O2"; then
       FCFLAGS=""
    fi
    if test -z "$DEBUG"; then
       DEBUG="-g"
    fi
    if test -z "$OPT"; then
       OPT="-O2"
    fi
#  Put ifort after gnu in case wrapper script mpifort
#  from openmpi is wrapping gnu.  Prevents misidentification
elif echo $ac_fc_version_output | grep -i 'intel.*fortran' >/dev/null 2>&1; then
   echo "Fortran Compiler is Intel ifort"
   CPRDEF="INTEL"
   if test -z "$REAL8"; then
      REAL8="-r8"
   fi
   if test "$FCFLAGS" = "$DEFFCFLAGS"; then
      FCFLAGS="-w -ftz"
   fi
   if test -z "$PROGFCFLAGS"; then
      PROGFCFLAGS="-assume byterecl"
   fi
   if test -z "$ENDIAN"; then
      ENDIAN="-convert big_endian"
   fi
   if test -z "$OPT"; then
      OPT="-O2"
   fi
   if test -z "$DEBUG"; then
      DEBUG="-g"
   fi
# Put ftn after GNU for the case where ftn is wrapping PGF
elif echo $FC | grep ftn >/dev/null 2>&1; then
 if echo $ac_fc_version_output | grep -i Portland >/dev/null 2>&1; then
   echo "Fortran Compiler is Portland Group, Cray"
   CPRDEF="PGI"
   SYSDEF="CNLINUX"
   if test -z "$REAL8"; then
      REAL8="-r8"
   fi
   if test -z "$BIT64"; then
      BIT64="-pc 64"
   fi
   if test "$FCFLAGS" = "$DEFFCFLAGS"; then
      FCFLAGS=""
   fi
   if test -z "$ENDIAN"; then
      ENDIAN="-byteswapio"
   fi
   if test -z "$OPT"; then
      OPT="-O2"
   fi
   if test -z "$DEBUG"; then
      DEBUG="-g"
   fi
 fi
elif echo $ac_fc_version_output | grep -i nag >/dev/null 2>&1; then
   echo "Fortran Compiler is NAG"
   CPRDEF="NAG"
   if test -z "$REAL8"; then
      REAL8="-r8"
   fi
   if test "$FCFLAGS" = "$DEFFCFLAGS"; then
      FCFLAGS="-wmismatch=mpi_send,mpi_recv,mpi_bcast,mpi_allreduce,mpi_reduce,mpi_gatherv,mpi_gather,mpi_rsend,mpi_irecv,mpi_isend,mpi_scatterv,mpi_alltoallv -dusty"
   fi
   if test -z "$ENDIAN"; then
      ENDIAN="-convert=BIG_IEEE"
   fi
   if test -z "$OPT"; then
      OPT="-O2"
   fi
   if test -z "$DEBUG"; then
      DEBUG="-g"
   fi
###########################################################
# the compiler flags below have not been verified recently
###########################################################
elif echo $FC | grep frt >/dev/null 2>&1; then
   echo "Fortran Compiler is UXP/V"
   echo "Suggested additional vectorization flags: -Wv,-s5,-t3,-noalias,-ilfunc,-md"
   CPRDEF="FUJITSU"
   if test -z "$F90FLAGS"; then
      F90FLAGS="-Am -X9"
   fi
   if test -z "$BIT64"; then
      BIT64="-KA64"
   fi
   if test -z "$REAL8"; then
      REAL8="-Ad"
   fi
elif echo $ac_fc_version_output | grep Lahey >/dev/null 2>&1; then
   echo "Fortran Compiler is Lahey"
   CPRDEF="LAHEY"
elif echo $FC | grep pathf90 >/dev/null 2>&1; then
   echo "Fortran Compiler is PathScale"
   CPRDEF="PATHSC"
   if test -z "$REAL8"; then
      REAL8="-r8"
   fi
   if test -z "$BIT64"; then
      BIT64="-m64"
   fi
   if test -z "$OPT"; then
      OPT="-O2"
   fi
elif echo $ac_fc_version_output | grep -i absoft >/dev/null 2>&1; then
   echo "Fortran Compiler is Absoft"
   CPRDEF="ABSOFT"
   if test -z "$REAL8"; then
      REAL8="-N113"
   fi
   if test -z "$INCLUDEFLAG"; then
      INCLUDEFLAG="-p"
   fi
   if test -z "$OPT"; then
      OPT="-O2"
   fi
elif echo $ac_fc_version_output | grep -i workshop >/dev/null 2>&1; then
   echo "Fortran Compiler is Workshop"
   CPRDEF="WORKSHOP"
   if test -z "$INCLUDEFLAG"; then
      INCLUDEFLAG="-M"
   fi
elif echo $ac_fc_version_output | grep -i mipspro >/dev/null 2>&1; then
   echo "Fortran Compiler is MIPSPro"
   CPRDEF="MIPSPRO"
   EXTRACFLAGS="-64"
   if test -z "$OPT"; then
      OPT="-O3"
   fi
   if test -z "$REAL8"; then
      REAL8="-r8"
   fi
   if test -z "$BIT64"; then
      BIT64="-64"
   fi
elif echo $ac_fc_version_output | grep -i compaq >/dev/null 2>&1; then
   echo "Fortran Compiler is Compaq"
   CPRDEF="COMPAQ"
   MPILIBS="$MPILIBS -lelan"
   if test -z "$OPT"; then
      OPT="-fast"
   fi
   if test -z "$REAL8"; then
      REAL8="-real_size 64"
   fi
   if test -z "$ENDIAN"; then
      ENDIAN="-convert big_endian"
   fi

# Compaq Fortran changed its name to HP Fortran.
# Lets support both versions for now.
elif echo $ac_fc_version_output | grep HP >/dev/null 2>&1; then
   echo "Fortran Compiler is HP"
   CPRDEF="COMPAQ"
   MPILIBS="$MPILIBS -lelan"
   if test -z "$OPT"; then
      OPT="-fast"
   fi
   if test -z "$REAL8"; then
      REAL8="-real_size 64"
   fi
   if test -z "$ENDIAN"; then
      ENDIAN="-convert big_endian"
   fi

elif echo $ac_fc_version_output | grep -i sx >/dev/null 2>&1; then
   echo "Fortran Compiler is SX"
   CPRDEF="SX"
   if test -z "$F90FLAGS"; then
      F90FLAGS="-EP -Wf'-pvctl noassoc'"
   fi
   if test -z "$OPT"; then
      OPT="-Chopt"
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


###########################################################
# END of compiler-specific flag setting
###########################################################

CPPDEFS="$CPPDEFS -DSYS$SYSDEF -DCPR$CPRDEF"
if test -n "$SRKDEF"; then
    CPPDEFS="$CPPDEFS -D$SRKDEF"
fi

# IF DEBUGGING ENABLED, DISABLE OPTIMIZATION FLAG
if test "$DEBUGGING" = "ENABLED"; then
        OPT=""
else
        DEBUG=""
fi

# SET HARDCODED VARIABLES AS A LAST RESORT

# ALWAYS ENABLE CRULE IN MAKEFILE
AC_SUBST(CRULE,[.c.o])

AC_SUBST(CPPDEFS)

# INCLUDE FLAG IF NOT ALREADY SET IS MOST LIKELY -I
if test -z "$INCLUDEFLAG"; then
   INCLUDEFLAG="-I"
fi

# ARCHIVE COMMAND SIMILAR ACROSS ALL PLATFORMS
if test -z "$AR"; then
   AR="ar cq"
fi

# RANLIB
if test -z "$RANLIB"; then
    # Necessary on Darwin to deal with common symbols (particularly when
    # using ifort).
    if test "$SYSDEF"x = DARWINx; then
        RANLIB="ranlib -c"
    else
        AC_PROG_RANLIB
    fi
fi

echo
echo Output Variables: {CC=$CC} {CFLAGS=$CFLAGS} \
{FC=$FC} {FCFLAGS=$FCFLAGS} {PROGFCFLAGS=$PROGFCFLAGS}\
{CPPDEFS=$CPPDEFS} {OPT=$OPT} {DEBUG=$DEBUG} {REAL8=$REAL8} \
{BIT64=$BIT64} {ENDIAN=$ENDIAN} {MPIFC=$MPIFC} \
{MPILIBS=$MPILIBS} {MPIHEADER=$MPIHEADER}  \
{INCLUDEFLAG=$INCLUDEFLAG} {INCLUDEPATH=$INCLUDEPATH} \
{AR=$AR} {RANLIB=$RANLIB} {BABELROOT=$BABELROOT} {COMPILER_ROOT=$COMPILER_ROOT} \
{PYTHON=$PYTHON} {PYTHONOPTS=$PYTHONOPTS} {FORT_SIZE=$FORT_SIZE} {prefix=$prefix} \
{SRCDIR=$SRCDIR} {FC_DEFINE=$FC_DEFINE}
echo

if test -n "$DONOTCHECKMPI"; then
   echo "MPISERIAL ENABLED: CONFIGURING mpi-serial"
   AC_CONFIG_SUBDIRS(mpi-serial)
fi

AC_OUTPUT

echo Please check the Makefile.conf
echo Have a nice day!

# test -z is true for empty strings
# test -n is true for non-empty strings




