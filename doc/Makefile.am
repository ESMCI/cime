# This is part of PIO. It creates the doc Makefile.

# Ed Hartnett 4/1/19

# Run doxygen, then confirm warning log file is empty.
check: all
all:
	doxygen Doxyfile
	[ ! -s doxywarn.log ]

SUBDIRS = source

CLEANFILES = *.log

EXTRA_DIST = CMakeLists.txt customdoxygen.css Doxyfile.in	\
DoxygenLayout.xml doxygen.sty
