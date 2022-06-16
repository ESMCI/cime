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

    -t=*|--test_root=*)
    test_root="${arg#*=}"
    shift
    ;;

esac
done
if [[ ${cime_root} == "default" ]]; then
    echo "Error: cime_root not set" >&2
    exit 1;
fi

if [[ ${test_root} == "default" ]]; then
    echo "Error: test_root not set" >&2
    exit 1;
fi

output_root=$PWD

# Add testing bin to path
PATH=${test_root}/bin:${PATH}

# We will redirect verbose test log output to a file; remove any existing
# versions of this file first
test_log=${PWD}/test.out
test_bin=${test_root}/bin
rm -f ${test_log}

# build prereqs
# Configure for local machine configuration files
echo about to call check_config_files.sh
echo cime_root=${cime_root}
echo test_root=${test_root}
${cime_root}/tools/mapping/tests/check_config_files.sh --cime_root=${cime_root} --test_root=${test_root} >> ${test_log} 2>&1
if [ $? != 0 ]; then
    echo "ERROR creating config files" >&2
    echo "cat ${test_log} for more info" >&2
    exit 1
fi

#check for GenerateVolumetricMesh in path. Build if necessary
${cime_root}/tools/mapping/tests/check_tempestremap.sh --cime_root=${cime_root} --test_root=${test_root} >> ${test_log} 2>&1
if [ $? != 0 ]; then
    echo "ERROR building TempestRemap" >&2
    echo "cat ${test_log} for more info" >&2
    exit 1
fi
generatevolumetricmesh=`which GenerateVolumetricMesh`
convertexodustoscrip=`which ConvertExodusToSCRIP`

ne4g=${cime_root}/tools/mapping/tests/reference_files/ne4.g

(. ${test_bin}/config_files/.env_mach_specific.sh && ${generatevolumetricmesh} --in ${ne4g} --out ne4pg2.g --np 2 --uniform) >> ${test_log} 2>&1
if [ ! -f ne4pg2.g ]; then
    echo "ERROR: GenerateVolumetricMesh: no ne4pg2.g file created" >&2
    echo "cat ${test_log} for more info" >&2
    exit 1
fi

(. ${test_bin}/config_files/.env_mach_specific.sh && ${convertexodustoscrip} --in ne4pg2.g --out ne4pg2.scrip.nc) >> ${test_log} 2>&1
if [ ! -f ne4pg2.scrip.nc ]; then
    echo "ERROR: ConvertExodusToSCRIP: no ne4pg2.scrip.nc file created" >&2
    echo "cat ${test_log} for more info" >&2
    exit 1
fi



exit 0
