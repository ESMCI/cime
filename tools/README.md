Tools
-----

Find quick descriptions of various tools under this directory and within the CIME python package.

cprnc
-----

The cprnc tool has been moved from this directory to CIME/non_py/cprnc.

CIME/Tools
----------

Various tools used to manipulate CIME cases.


load_balancing_tool
-------------------

Tool to find reasonable PE layouts from timing files.

MakeRedsky.sh
-------------

Helper script for redsky machine.

mapping/check_maps
------------------

Tool to check previously generated mapping files.

mapping/gen_domain_files
------------------------

The gen_domain tool will read in a conservative ocean to atemosphere map file and output three domain files; an ocean domain, land domain with land mask and land domain with ocean mask.

mapping/gen_mapping_files
-------------------------

Tool to generate a suite of mapping files to map between specified grid files.

mapping/gridplot.sh
-------------------

Script to plot SCRIB files.

mapping/map_field
-----------------

The map_field tool will read a mapping file and input field to output a mapping between them.

statisical_ensemble_test
------------------------

CESM-ECT is a suite of tests to determine whether a new simulation setup is statistically distringuishable from an acccepted ensemble.

utils/find_circular_dependency.py
---------------------------------

Tool will look for circular dependencies in CESM "Depends" files.
