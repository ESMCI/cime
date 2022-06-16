#!/bin/bash

# get arguments
# Need --cime_root=
#      --test_root=


cime_root="default"
test_root="default"

for arg in "$@"
do
case $arg in
    -c=*|--cime_root=*)
    cime_root="${arg#*=}"
    shift
    ;;

esac
done
if [[ ${cime_root} == "default" ]]; then
    echo "Error: cime_root not set" >&2
    exit 1;
fi

output_root=$PWD

# We will redirect verbose test log output to a file; remove any existing
# versions of this file first
test_log=${PWD}/test.out
rm -f ${test_log}

generatecsmesh=`which GenerateCSMesh`

rm -f ne4.g
(${generatecsmesh} --alt --res 4 --file ${output_root}/ne4.g) >> ${test_log} 2>&1
if [ ! -f ne4.g ]; then
    echo "ERROR: no ne4.g file created" >&2
    echo "cat ${test_log} for more info" >&2
    exit 1
fi

exit 0
