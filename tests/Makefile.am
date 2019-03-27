# This file is part of PIO. It generates the Makefiles for the tests
# directory.

# Ed Hartnett

# Does the user want to build fortran? If so, there are two additional
# test directories.
if BUILD_FORTRAN
UNIT = unit
GENERAL = general
endif

SUBDIRS = cunit ${UNIT} ${GENERAL}

EXTRA_DIST = CMakeLists.txt
