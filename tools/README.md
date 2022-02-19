# Tools

Find quick descriptions of various tools under this directory and within the CIME python package.

## CIME/Tools

Various tools used to manipulate CIME cases.

[CIME/Tools](../CIME/Tools)

## cprnc

Generic tool for analyzing a netcdf file or comparing two netcdf files.

[README](../CIME/non_py/cprnc/README)
[cprnc](../CIME/non_py/cprnc)

## load_balancing_tool

Tool to find reasonable PE layouts from timing files.

[README](load_balancing_tool/README)
[load_balancing_tool](load_balancing_tool)

## MakeRedsky.sh

Helper script for redsky machine.

[MakeRedsky.sh](MakeRedsky.sh)

## mapping

Various tools related to mapping.

### check_maps

Tool to check previously generated mapping files. See `README` for more details.

[README](mapping/check_maps/README)
[check_maps](mapping/check_maps)

### gen_domain_files

The `gen_domain` tool will read in a conservative ocean to atemosphere map file and output three domain files; an ocean domain, land domain with land mask and land domain with ocean mask.

[README](mapping/gen_domain_files/README)
[gen_domain_files](mapping/gen_domain_files)

### gen_mapping_files

Tool to generate a suite of mapping files to map between specified grid files. See `README` for more details.

[README](mapping/gen_mapping_files/README)
[gen_mapping_files](mapping/gen_mapping_files)

### gridplot.sh

Script to plot SCRIB files.

### map_field

The `map_fields` tool will read a mapping file and input field to output a mapping between them.

[README](mapping/map_field/README)
[map_field](mapping/map_field)

## statisical_ensemble_test

CESM-ECT is a suite of tests to determine whether a new simulation setup is statistically distringuishable from an acccepted ensemble.

[README](statisical_ensemble_test/README)
[statisical_ensemble_test](statisical_ensemble_test)

## utils

### find_circular_dependency.py

Tool will look for circular dependencies in CESM `Depends` files.

[find_circular_dependency.py](utils/find_circular_dependency.py)
