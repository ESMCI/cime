#!/bin/sh
# This is a test script for PIO for tests/general directory.
# Ed Hartnett 3/25/19

# Stop execution of script if error is returned.
set -e

# Stop loop if ctrl-c is pressed.
trap exit INT TERM

printf 'running PIO tests...\n'

PIO_TESTS='pio_init_finalize pio_file_simple_tests pio_file_fail '\
'ncdf_simple_tests'

success1=true
for TEST in $PIO_TESTS
do
    success1=false
    echo "running ${TEST}"
    mpiexec -n 4 ./${TEST} && success1=true || break
done

# Did we succeed?
if test x$success1 = xtrue; then
    exit 0
fi
exit 1
